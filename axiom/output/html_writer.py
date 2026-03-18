import json
import re
from pathlib import Path
from typing import Dict, List

from axiom.core.models import ProjectIndex
from axiom.analysis.project_graph import (
    build_file_dependency_graph,
    find_dead_code,
    find_circular_imports,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _mid(name: str) -> str:
    """Sanitise a string into a valid Mermaid/HTML node id."""
    return re.sub(r"[^a-zA-Z0-9]", "_", name)


def _complexity_color(score: int) -> str:
    if score <= 5:   return "#3fb950"
    if score <= 10:  return "#8b949e"
    if score <= 15:  return "#d29922"
    if score <= 25:  return "#e3b341"
    return "#f85149"


def _severity_badge(severity: str) -> str:
    colors = {"low": "#d29922", "medium": "#e3b341", "high": "#f85149"}
    color = colors.get(severity, "#8b949e")
    return f'<span class="badge" style="background:{color}22;color:{color};border:1px solid {color}55">{severity}</span>'


def _short(path: str) -> str:
    return Path(path).name


# ── mermaid builders ─────────────────────────────────────────────────────────

def _mermaid_dep_graph(dependencies: Dict[str, List[str]]) -> str:
    lines = ["graph TD"]
    has_edges = False
    for src, targets in dependencies.items():
        for tgt in targets:
            s, t = _mid(_short(src)), _mid(_short(tgt))
            lines.append(f'    {s}["{_short(src)}"] --> {t}["{_short(tgt)}"]')
            has_edges = True
    if not has_edges:
        lines.append('    note["No intra-project imports detected"]')
    return "\n".join(lines)


def _mermaid_call_graph(call_graph: Dict) -> str:
    lines = ["graph LR"]
    has_edges = False
    for caller, callees in call_graph.items():
        for callee in sorted(callees)[:8]:   # cap at 8 callees per fn for readability
            lines.append(f"    {_mid(caller)}[\"{caller}\"] --> {_mid(callee)}[\"{callee}\"]")
            has_edges = True
    if not has_edges:
        return ""
    return "\n".join(lines)


# ── section builders ─────────────────────────────────────────────────────────

def _dashboard_stats(project: ProjectIndex, dead: Dict, circles: List) -> str:
    files = list(project.files.values())
    total_fns = sum(len([s for s in f.symbols if s.symbol_type == "function"]) for f in files)
    total_smells = sum(len(f.smells) for f in files)
    avg_complexity = round(sum(f.complexity for f in files) / max(len(files), 1), 1)
    dead_count = sum(len(v) for v in dead.values())

    def card(label, value, color="#58a6ff"):
        return f"""
        <div class="stat-card">
            <div class="stat-value" style="color:{color}">{value}</div>
            <div class="stat-label">{label}</div>
        </div>"""

    return f"""
    <div class="stat-row">
        {card("Python Files", len(files))}
        {card("Functions", total_fns)}
        {card("Avg Complexity", avg_complexity, _complexity_color(int(avg_complexity)))}
        {card("Code Smells", total_smells, "#f85149" if total_smells else "#3fb950")}
        {card("Dead Functions", dead_count, "#d29922" if dead_count else "#3fb950")}
        {card("Import Cycles", len(circles), "#f85149" if circles else "#3fb950")}
    </div>"""


def _complexity_chart_data(project: ProjectIndex) -> str:
    files = sorted(project.files.values(), key=lambda f: f.complexity, reverse=True)[:20]
    labels = json.dumps([_short(f.path) for f in files])
    data   = json.dumps([f.complexity for f in files])
    colors = json.dumps([_complexity_color(f.complexity) for f in files])
    return f"""
    new Chart(document.getElementById('complexityChart'), {{
        type: 'bar',
        data: {{
            labels: {labels},
            datasets: [{{
                label: 'Complexity',
                data: {data},
                backgroundColor: {colors},
                borderRadius: 4,
                borderSkipped: false,
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: ctx => ` Complexity: ${{ctx.raw}}`
                    }}
                }}
            }},
            scales: {{
                x: {{
                    grid: {{ color: '#21262d' }},
                    ticks: {{ color: '#8b949e' }}
                }},
                y: {{
                    grid: {{ color: '#21262d' }},
                    ticks: {{ color: '#c9d1d9', font: {{ family: 'JetBrains Mono', size: 11 }} }}
                }}
            }}
        }}
    }});"""


def _file_cards(project: ProjectIndex) -> str:
    files = sorted(project.files.values(), key=lambda f: f.complexity, reverse=True)
    cards = []
    for code_file in files:
        name = _short(code_file.path)
        fid  = _mid(code_file.path)

        # smell badges
        smell_html = ""
        if code_file.smells:
            badges = " ".join(_severity_badge(s.severity) + f" {s.name}" for s in code_file.smells)
            smell_html = f'<div class="smell-row">{badges}</div>'

        # complexity badge colour
        cc = _complexity_color(code_file.complexity)

        # call graph mermaid
        cg_mermaid = _mermaid_call_graph(code_file.call_graph)
        cg_block = ""
        if cg_mermaid:
            cg_block = f"""
            <div class="subsection">
                <div class="subsection-title">Call Graph</div>
                <pre class="mermaid">{cg_mermaid}</pre>
            </div>"""

        # functions table
        fn_rows = ""
        if code_file.symbols:
            for sym in sorted(code_file.symbols, key=lambda s: s.lineno):
                doc = (sym.docstring or "—")[:80]
                icon = "⚡" if sym.symbol_type == "function" else "🔷"
                priority = code_file.priority.get(sym.name, 0)
                p_color = _complexity_color(int(priority))
                fn_rows += f"""
                <tr>
                    <td class="mono">{icon} {sym.name}</td>
                    <td class="mono muted">L{sym.lineno}</td>
                    <td class="muted small">{doc}</td>
                    <td><span style="color:{p_color}" class="mono">{priority}</span></td>
                </tr>"""

        fn_block = ""
        if fn_rows:
            fn_block = f"""
            <div class="subsection">
                <div class="subsection-title">Symbols</div>
                <table class="fn-table">
                    <thead><tr><th>Name</th><th>Line</th><th>Docstring</th><th>Priority</th></tr></thead>
                    <tbody>{fn_rows}</tbody>
                </table>
            </div>"""

        # imports
        imp_block = ""
        if code_file.imports:
            imp_pills = " ".join(f'<span class="pill">{i}</span>' for i in code_file.imports[:20])
            imp_block = f'<div class="subsection"><div class="subsection-title">Imports</div><div class="pill-row">{imp_pills}</div></div>'

        cards.append(f"""
        <div class="file-card" id="file-{fid}">
            <div class="file-header">
                <div>
                    <span class="file-name">{name}</span>
                    <span class="file-path muted">{code_file.path}</span>
                </div>
                <div class="file-meta">
                    <span class="complexity-badge" style="color:{cc};border-color:{cc}55">
                        ⚙ {code_file.complexity}
                    </span>
                    <span class="muted small">{len(code_file.symbols)} symbols</span>
                </div>
            </div>
            {smell_html}
            {cg_block}
            {fn_block}
            {imp_block}
        </div>""")

    return "\n".join(cards)


def _dead_code_section(dead: Dict[str, List[str]]) -> str:
    if not dead:
        return '<div class="empty-state">✅ No dead code detected.</div>'
    rows = ""
    for path, fns in dead.items():
        for fn in fns:
            rows += f"""
            <div class="dead-row">
                <span class="mono" style="color:#f85149">{fn}</span>
                <span class="muted small">{_short(path)}</span>
            </div>"""
    return f'<div class="dead-list">{rows}</div>'


def _circular_imports_section(circles: List[List[str]]) -> str:
    if not circles:
        return '<div class="empty-state">✅ No circular imports detected.</div>'
    items = ""
    for cycle in circles:
        chain = " → ".join(f'<span class="mono">{_short(p)}</span>' for p in cycle)
        items += f'<div class="cycle-row">🔄 {chain}</div>'
    return f'<div class="cycle-list">{items}</div>'


def _sidebar_file_links(project: ProjectIndex) -> str:
    files = sorted(project.files.values(), key=lambda f: f.complexity, reverse=True)
    links = ""
    for f in files:
        name = _short(f.path)
        fid  = _mid(f.path)
        cc   = _complexity_color(f.complexity)
        dot  = f'<span style="color:{cc}">●</span>'
        links += f'<a href="#file-{fid}" class="sidebar-file">{dot} {name}</a>\n'
    return links


# ── main entry ────────────────────────────────────────────────────────────────

def write_html(project: ProjectIndex, output_path: str) -> None:
    project_name = Path(list(project.files.keys())[0]).parts[0] if project.files else "Project"

    dependencies  = build_file_dependency_graph(project)
    dead          = find_dead_code(project)
    circles       = find_circular_imports(dependencies)

    dep_mermaid   = _mermaid_dep_graph(dependencies)
    stats_html    = _dashboard_stats(project, dead, circles)
    chart_js      = _complexity_chart_data(project)
    file_cards    = _file_cards(project)
    dead_html     = _dead_code_section(dead)
    circles_html  = _circular_imports_section(circles)
    sidebar_links = _sidebar_file_links(project)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Axiom Report — {project_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
</script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --bg: #0d1117; --surface: #161b22; --surface2: #1c2128;
    --border: #30363d; --text: #e6edf3; --muted: #8b949e;
    --accent: #58a6ff; --green: #3fb950; --yellow: #d29922;
    --orange: #e3b341; --red: #f85149;
    --radius: 8px; --font: 'Inter', sans-serif; --mono: 'JetBrains Mono', monospace;
  }}
  html {{ scroll-behavior: smooth; }}
  body {{ background: var(--bg); color: var(--text); font-family: var(--font); display: flex; min-height: 100vh; }}

  /* sidebar */
  .sidebar {{
    width: 240px; min-height: 100vh; background: var(--surface);
    border-right: 1px solid var(--border); padding: 24px 16px;
    position: sticky; top: 0; height: 100vh; overflow-y: auto;
    flex-shrink: 0; display: flex; flex-direction: column; gap: 8px;
  }}
  .sidebar-logo {{ font-size: 18px; font-weight: 700; color: var(--accent); margin-bottom: 8px; letter-spacing: -0.5px; }}
  .sidebar-logo span {{ color: var(--muted); font-weight: 400; }}
  .sidebar-section {{ font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase;
    letter-spacing: 0.8px; margin: 16px 0 4px; padding: 0 8px; }}
  .sidebar a {{
    display: block; padding: 6px 8px; border-radius: 6px; text-decoration: none;
    color: var(--muted); font-size: 13px; transition: all 0.15s;
  }}
  .sidebar a:hover {{ background: var(--surface2); color: var(--text); }}
  .sidebar-file {{ font-family: var(--mono); font-size: 11px !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

  /* main */
  .main {{ flex: 1; padding: 32px 40px; max-width: 1200px; overflow-x: hidden; }}
  .page-title {{ font-size: 28px; font-weight: 700; margin-bottom: 4px; }}
  .page-sub {{ color: var(--muted); font-size: 14px; margin-bottom: 32px; }}

  /* sections */
  .section {{ margin-bottom: 48px; }}
  .section-title {{ font-size: 20px; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 10px; }}
  .section-title span {{ font-size: 14px; color: var(--muted); font-weight: 400; }}

  /* stat cards */
  .stat-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 32px; }}
  .stat-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; text-align: center; }}
  .stat-value {{ font-size: 32px; font-weight: 700; font-family: var(--mono); }}
  .stat-label {{ font-size: 12px; color: var(--muted); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}

  /* charts */
  .chart-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; margin-bottom: 24px; }}
  .chart-title {{ font-size: 14px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px; }}
  .chart-container {{ height: 320px; position: relative; }}

  /* mermaid */
  .mermaid-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; overflow-x: auto; }}
  pre.mermaid {{ background: transparent !important; }}

  /* file cards */
  .file-card {{
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    margin-bottom: 16px; overflow: hidden; transition: border-color 0.2s;
  }}
  .file-card:hover {{ border-color: #58a6ff44; }}
  .file-header {{
    display: flex; justify-content: space-between; align-items: flex-start;
    padding: 20px 24px 16px; border-bottom: 1px solid var(--border);
  }}
  .file-name {{ font-size: 16px; font-weight: 600; font-family: var(--mono); display: block; }}
  .file-path {{ font-size: 11px; display: block; margin-top: 2px; }}
  .file-meta {{ display: flex; align-items: center; gap: 12px; flex-shrink: 0; }}
  .complexity-badge {{
    font-family: var(--mono); font-size: 13px; font-weight: 600;
    padding: 4px 10px; border-radius: 20px; border: 1px solid; background: transparent;
  }}

  /* smells */
  .smell-row {{ padding: 10px 24px; background: var(--surface2); border-bottom: 1px solid var(--border); display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
  .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; font-family: var(--mono); }}

  /* subsections */
  .subsection {{ padding: 16px 24px; border-bottom: 1px solid var(--border); }}
  .subsection:last-child {{ border-bottom: none; }}
  .subsection-title {{ font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 12px; }}

  /* table */
  .fn-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .fn-table th {{ text-align: left; color: var(--muted); font-size: 11px; font-weight: 500; padding: 6px 8px; border-bottom: 1px solid var(--border); }}
  .fn-table td {{ padding: 7px 8px; border-bottom: 1px solid #21262d; vertical-align: top; }}
  .fn-table tr:last-child td {{ border-bottom: none; }}
  .fn-table tr:hover td {{ background: var(--surface2); }}

  /* pills */
  .pill-row {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .pill {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 4px; padding: 2px 8px; font-size: 11px; font-family: var(--mono); color: var(--muted); }}

  /* dead code / cycles */
  .dead-list, .cycle-list {{ display: flex; flex-direction: column; gap: 8px; }}
  .dead-row, .cycle-row {{
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 12px 16px; display: flex; align-items: center; gap: 16px;
  }}
  .empty-state {{ color: var(--muted); font-size: 14px; padding: 24px; text-align: center; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }}

  /* utils */
  .mono {{ font-family: var(--mono); }}
  .muted {{ color: var(--muted); }}
  .small {{ font-size: 12px; }}

  /* scrollbar */
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
</style>
</head>
<body>

<aside class="sidebar">
  <div class="sidebar-logo">⬡ Axiom<span>-Code</span></div>
  <a href="#dashboard">📊 Dashboard</a>
  <a href="#dep-graph">🗺 Dependency Graph</a>
  <a href="#dead-code">💀 Dead Code</a>
  <a href="#circular">🔄 Circular Imports</a>
  <div class="sidebar-section">Files</div>
  {sidebar_links}
</aside>

<main class="main">
  <div class="page-title">Axiom Report</div>
  <div class="page-sub mono muted">{project_name}</div>

  <!-- DASHBOARD -->
  <section class="section" id="dashboard">
    <div class="section-title">📊 Dashboard</div>
    {stats_html}
    <div class="chart-card">
      <div class="chart-title">Complexity by File</div>
      <div class="chart-container">
        <canvas id="complexityChart"></canvas>
      </div>
    </div>
  </section>

  <!-- DEPENDENCY GRAPH -->
  <section class="section" id="dep-graph">
    <div class="section-title">🗺 Dependency Graph <span>intra-project imports</span></div>
    <div class="mermaid-card">
      <pre class="mermaid">{dep_mermaid}</pre>
    </div>
  </section>

  <!-- FILES -->
  <section class="section" id="files">
    <div class="section-title">📁 Files <span>sorted by complexity</span></div>
    {file_cards}
  </section>

  <!-- DEAD CODE -->
  <section class="section" id="dead-code">
    <div class="section-title">💀 Dead Code <span>public functions never called</span></div>
    {dead_html}
  </section>

  <!-- CIRCULAR IMPORTS -->
  <section class="section" id="circular">
    <div class="section-title">🔄 Circular Imports</div>
    {circles_html}
  </section>

</main>

<script>
{chart_js}
</script>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
