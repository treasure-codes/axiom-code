import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from axiom.core.models import ProjectIndex
from axiom.analysis.project_graph import (
    build_file_dependency_graph,
    find_dead_code,
    find_circular_imports,
)


# ── utilities ──────────────────────────────────────────────────────────────────

def _safe_id(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "_", name)


def _short(path: str) -> str:
    return Path(path).name


def _is_noise_path(path: str) -> bool:
    p = Path(path)
    name = p.name.lower()
    parts_lower = [pt.lower() for pt in p.parts]
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or "test" in parts_lower
        or "tests" in parts_lower
        or "migration" in name
        or "alembic" in name
        or "versions" in parts_lower
    )


def _cx_color(score: int) -> str:
    if score <= 5:   return "var(--green)"
    if score <= 10:  return "var(--muted)"
    if score <= 20:  return "var(--amber)"
    return "var(--red)"


def _effort(complexity: int) -> Tuple[str, str]:
    """Returns (label, css_class)."""
    if complexity <= 8:  return "SMALL",  "green"
    if complexity <= 18: return "MEDIUM", "amber"
    return "LARGE", "red"


def _health_score(project: ProjectIndex, circles: List) -> int:
    score = 100
    for f in project.files.values():
        for smell in f.smells:
            score -= {"high": 6, "medium": 3, "low": 1}.get(smell.severity, 1)
        if f.complexity > 25:
            score -= 6
        elif f.complexity > 15:
            score -= 2
    score -= len(circles) * 10
    return max(0, min(100, int(score)))


def _health_color(score: int) -> str:
    if score >= 80: return "var(--green)"
    if score >= 60: return "var(--amber)"
    return "var(--red)"


def _health_label(score: int) -> str:
    if score >= 80: return "Healthy"
    if score >= 60: return "Fair"
    if score >= 40: return "Needs work"
    return "Critical"


# ── brief ──────────────────────────────────────────────────────────────────────

def _generate_brief(
    project: ProjectIndex,
    real_dead: Dict,
    circles: List,
    dependencies: Dict,
) -> str:
    files = list(project.files.values())
    if not files:
        return "No Python files were found in this project."

    total_fns   = sum(1 for f in files for s in f.symbols if s.symbol_type == "function")
    total_smells = sum(len(f.smells) for f in files)
    riskiest    = max(files, key=lambda f: f.complexity)
    clean       = [f for f in files if f.complexity <= 5 and not f.smells]
    riskiest_importers = sum(1 for deps in dependencies.values() if riskiest.path in deps)

    sentences = []
    sentences.append(
        f"This project has <strong>{len(files)}</strong> files and "
        f"<strong>{total_fns}</strong> functions."
    )

    if riskiest.complexity > 20:
        importers_note = (
            f", imported by {riskiest_importers} other files"
            if riskiest_importers > 0 else ""
        )
        sentences.append(
            f"Your highest-risk file is <code>{_short(riskiest.path)}</code> "
            f"(complexity&nbsp;{riskiest.complexity}{importers_note}) — "
            f"this is the most likely source of bugs and the hardest to change safely."
        )
    elif riskiest.complexity > 10:
        sentences.append(
            f"Complexity is moderate — the most complex file is "
            f"<code>{_short(riskiest.path)}</code> at {riskiest.complexity}."
        )
    else:
        sentences.append(
            "Complexity is low across the board — this codebase is easy to navigate."
        )

    if clean:
        clean_names = ", ".join(f"<code>{_short(f.path)}</code>" for f in clean[:3])
        sentences.append(f"The good news: {clean_names} are clean.")

    if circles:
        sentences.append(
            f"<strong>{len(circles)} import "
            f"cycle{'s' if len(circles) > 1 else ''}</strong> detected — "
            f"these block safe refactoring and should be resolved first."
        )
    else:
        sentences.append("Zero circular imports — the dependency graph is clean.")

    if total_smells == 0:
        sentences.append("No code smells detected.")
    elif total_smells <= 3:
        sentences.append(
            f"{total_smells} minor code smell{'s' if total_smells > 1 else ''} found."
        )
    else:
        sentences.append(
            f"{total_smells} code smells found — prioritise the high-severity ones first."
        )

    return " ".join(sentences)


# ── actions ────────────────────────────────────────────────────────────────────

def _build_actions(
    project: ProjectIndex, real_dead: Dict, circles: List
) -> List[Dict]:
    actions = []
    files = list(project.files.values())

    for cycle in circles:
        chain = " → ".join(_short(p) for p in cycle)
        actions.append({
            "level":      "critical",
            "title":      "Import cycle",
            "detail":     chain,
            "file":       _short(cycle[0]),
            "effort":     "MEDIUM",
            "effort_cls": "amber",
            "anchor":     "dep-map",
        })

    for f in sorted(files, key=lambda x: x.complexity, reverse=True):
        if f.complexity <= 10:
            break
        elabel, ecls = _effort(f.complexity)
        tier = "critical" if f.complexity > 20 else "important"
        actions.append({
            "level":      tier,
            "title":      f"High complexity ({f.complexity})",
            "detail":     f"{f.complexity} branch points — hard to reason about and test reliably.",
            "file":       _short(f.path),
            "effort":     elabel,
            "effort_cls": ecls,
            "anchor":     f"file-{_safe_id(f.path)}",
        })

    for f in files:
        for smell in f.smells:
            tier = "critical" if smell.severity == "high" else "important"
            elabel, ecls = _effort(f.complexity)
            actions.append({
                "level":      tier,
                "title":      smell.name,
                "detail":     smell.message,
                "file":       _short(f.path),
                "effort":     elabel,
                "effort_cls": ecls,
                "anchor":     f"file-{_safe_id(f.path)}",
            })

    total_dead = sum(len(v) for v in real_dead.values())
    if total_dead > 0:
        preview_items = []
        for path, fns in real_dead.items():
            preview_items.extend(f"{fn} ({_short(path)})" for fn in fns[:2])
        preview = ", ".join(preview_items[:4])
        if total_dead > 4:
            preview += f" +{total_dead - 4} more"
        actions.append({
            "level":      "cleanup",
            "title":      f"{total_dead} potentially unreachable function{'s' if total_dead > 1 else ''}",
            "detail":     preview,
            "file":       None,
            "effort":     "SMALL",
            "effort_cls": "green",
            "anchor":     "dead-code",
        })

    return actions


# ── render: triage ─────────────────────────────────────────────────────────────

def _render_triage(actions: List[Dict]) -> str:
    if not actions:
        return '<p class="empty">No issues found — this codebase is in great shape.</p>'

    level_colors = {
        "critical":  "var(--red)",
        "important": "var(--amber)",
        "cleanup":   "var(--muted)",
    }

    rows = ""
    for item in actions:
        dot_color  = level_colors.get(item["level"], "var(--muted)")
        file_chip  = (
            f'<span class="chip mono">{item["file"]}</span>'
            if item["file"] else ""
        )
        effort_chip = f'<span class="chip {item["effort_cls"]}">{item["effort"]}</span>'
        rows += f"""
        <a class="row" href="#{item['anchor']}">
          <span class="dot" style="background:{dot_color}"></span>
          <span class="row-body">
            <span class="row-title">{item['title']}</span>
            <span class="row-detail">{item['detail']}</span>
          </span>
          <span class="row-end">{file_chip}{effort_chip}<span class="chev">&#8250;</span></span>
        </a>"""

    return f'<div class="row-list">{rows}</div>'


# ── render: files ──────────────────────────────────────────────────────────────

def _render_files(project: ProjectIndex) -> str:
    files = sorted(project.files.values(), key=lambda f: f.complexity, reverse=True)
    rows  = ""

    for f in files:
        fid    = _safe_id(f.path)
        name   = _short(f.path)
        cx     = f.complexity
        cx_col = _cx_color(cx)

        if cx > 20 or any(s.severity == "high" for s in f.smells):
            risk      = "risky"
            dot_color = "var(--red)"
        elif cx <= 5 and not f.smells:
            risk      = "safe"
            dot_color = "var(--green)"
        else:
            risk      = "moderate"
            dot_color = "var(--amber)"

        fn_count    = sum(1 for s in f.symbols if s.symbol_type == "function")
        class_count = sum(1 for s in f.symbols if s.symbol_type == "class")

        cx_badge = ""
        if cx > 20:
            cx_badge = '<span class="chip red">High complexity</span>'
        elif cx > 10:
            cx_badge = '<span class="chip amber">Elevated</span>'

        sym_rows = ""
        for sym in sorted(f.symbols, key=lambda s: s.lineno):
            callee_count = len(f.call_graph.get(sym.name, set()))
            doc          = (sym.docstring or "")[:80]
            icon         = "&#402;" if sym.symbol_type == "function" else "C"
            icon_color   = "var(--blue)" if sym.symbol_type == "function" else "var(--purple)"
            sym_rows += f"""
                <tr>
                  <td><span style="color:{icon_color};font-family:var(--mono);font-size:11px">{icon}</span>&nbsp;<span class="mono">{sym.name}</span></td>
                  <td class="mono muted">L{sym.lineno}</td>
                  <td class="muted trunc">{doc}</td>
                  <td class="mono muted">{callee_count}c</td>
                </tr>"""

        detail_inner = ""
        if sym_rows:
            detail_inner += f"""<table class="sym-table">
              <thead><tr><th>Symbol</th><th>Line</th><th>Purpose</th><th>Calls</th></tr></thead>
              <tbody>{sym_rows}</tbody>
            </table>"""

        if f.imports:
            pills         = "".join(
                f'<span class="chip mono">{i}</span>' for i in f.imports[:20]
            )
            detail_inner += f'<div class="pill-row">{pills}</div>'

        rows += f"""
        <div class="file-row" id="file-{fid}" data-name="{name.lower()}" data-risk="{risk}">
          <button class="file-hd" onclick="toggleFile('{fid}')">
            <span class="dot" style="background:{dot_color}"></span>
            <span class="file-name mono">{name}</span>
            <span class="file-cx mono" style="color:{cx_col}">{cx}</span>
            {cx_badge}
            <span class="muted small">{fn_count}f&nbsp;{class_count}c</span>
            <span class="chev" id="chev-{fid}">&#8250;</span>
          </button>
          <div class="file-detail" id="det-{fid}">{detail_inner}</div>
        </div>"""

    return rows


# ── render: dependency hubs ────────────────────────────────────────────────────

def _render_dep_hubs(dependencies: Dict, project: ProjectIndex) -> str:
    counts: Dict[str, int] = {}
    for path in project.files:
        n = sum(1 for deps in dependencies.values() if path in deps)
        if n > 0:
            counts[path] = n

    if not counts:
        return '<p class="empty">No intra-project imports detected.</p>'

    sorted_hubs = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    max_n       = sorted_hubs[0][1]

    cards = ""
    for path, n in sorted_hubs:
        fid       = _safe_id(path)
        pct       = int(n / max_n * 100)
        bar_color = (
            "var(--red)"   if pct >= 70 else
            "var(--amber)" if pct >= 40 else
            "var(--muted)"
        )
        cards += f"""
        <a class="hub-card" href="#file-{fid}">
          <div class="mono hub-name">{_short(path)}</div>
          <div class="hub-count">imported by {n} file{"s" if n != 1 else ""}</div>
          <div class="hub-bar"><div style="width:{pct}%;height:100%;background:{bar_color}"></div></div>
        </a>"""

    return f'<div class="hub-grid">{cards}</div>'


# ── render: dead code ──────────────────────────────────────────────────────────

def _render_dead_code(dead: Dict) -> str:
    real_dead   = {p: fns for p, fns in dead.items() if not _is_noise_path(p)}
    noise_count = sum(len(v) for p, v in dead.items() if _is_noise_path(p))
    total_real  = sum(len(v) for v in real_dead.values())

    warning = (
        '<div class="callout">'
        "Static analysis cannot see external callers. pytest functions, Alembic migration "
        "hooks, FastAPI route handlers, and Pydantic validators appear here even though they "
        "are actively used. Cross-reference with your test runner and framework before "
        "deleting anything."
        "</div>"
    )

    if not real_dead and not noise_count:
        return '<p class="empty">No dead code detected — every public function is reachable.</p>'

    if not real_dead:
        return (
            f"{warning}"
            f'<p class="empty">No dead code in production files. '
            f'<span class="muted">{noise_count} functions in test/migration files '
            f"excluded — expected.</span></p>"
        )

    rows = ""
    for path, fns in sorted(real_dead.items()):
        fid = _safe_id(path)
        for fn in fns:
            rows += f"""
            <div class="dead-row">
              <span class="mono">{fn}</span>
              <a class="chip mono" href="#file-{fid}">{_short(path)}</a>
            </div>"""

    noise_note = (
        f'<p class="muted small" style="margin-top:10px">'
        f"{noise_count} additional functions in test/migration files excluded — expected.</p>"
    ) if noise_count else ""

    return f"""{warning}
    <div class="collapse-wrap">
      <button class="collapse-btn" onclick="toggleDead()">
        <span>Show {total_real} symbol{"s" if total_real != 1 else ""}</span>
        <span class="chev" id="dead-chev">&#8250;</span>
      </button>
      <div class="dead-list" id="dead-list">{rows}</div>
    </div>
    {noise_note}"""


# ── render: circular imports ───────────────────────────────────────────────────

def _render_circles(circles: List, file_count: int) -> str:
    if not circles:
        return (
            f'<div class="success-bar">'
            f"&#10003;&nbsp; No circular imports detected across {file_count} files."
            f"</div>"
        )

    rows = ""
    for cycle in circles:
        chain = " &#8594; ".join(_short(p) for p in cycle)
        rows += f'<div class="cycle-row"><span class="mono">{chain}</span></div>'

    return f'<div class="cycle-list">{rows}</div>'


# ── main entry ─────────────────────────────────────────────────────────────────

def write_html(project: ProjectIndex, output_path: str) -> None:
    project_name = (
        Path(list(project.files.keys())[0]).parts[0]
        if project.files else "Project"
    )

    dependencies = build_file_dependency_graph(project)
    dead         = find_dead_code(project)
    circles      = find_circular_imports(dependencies)
    real_dead    = {p: fns for p, fns in dead.items() if not _is_noise_path(p)}

    health  = _health_score(project, circles)
    h_color = _health_color(health)
    h_label = _health_label(health)
    brief   = _generate_brief(project, real_dead, circles, dependencies)
    actions = _build_actions(project, real_dead, circles)

    triage_html  = _render_triage(actions)
    files_html   = _render_files(project)
    dep_html     = _render_dep_hubs(dependencies, project)
    dead_html    = _render_dead_code(dead)
    circles_html = _render_circles(circles, len(project.files))

    total_fns    = sum(
        1 for f in project.files.values()
        for s in f.symbols if s.symbol_type == "function"
    )
    total_smells = sum(len(f.smells) for f in project.files.values())
    real_dead_n  = sum(len(v) for v in real_dead.values())
    avg_cx_raw   = (
        sum(f.complexity for f in project.files.values()) / max(len(project.files), 1)
    )
    avg_cx       = round(avg_cx_raw, 1)
    n_files      = len(project.files)
    n_findings   = len(actions)
    generated    = datetime.now().strftime("%Y-%m-%d %H:%M")

    smells_color  = "var(--red)"   if total_smells else "var(--text)"
    circles_color = "var(--red)"   if circles      else "var(--text)"
    dead_color    = "var(--amber)" if real_dead_n  else "var(--text)"
    avg_cx_color  = _cx_color(int(avg_cx_raw))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Axiom &#8212; {project_name}</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --bg:     #0F1117;
  --surf:   #161B22;
  --brd:    #21262D;
  --text:   #E6EDF3;
  --muted:  #7D8590;
  --faint:  #30363D;
  --red:    #E24B4A;
  --amber:  #D29922;
  --green:  #3FB950;
  --blue:   #58A6FF;
  --purple: #BC8CFF;
  --font:   system-ui, -apple-system, sans-serif;
  --mono:   ui-monospace, 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
}}

@media (prefers-color-scheme: light) {{
  :root {{
    --bg:     #FFFFFF;
    --surf:   #F6F8FA;
    --brd:    #D0D7DE;
    --text:   #1F2328;
    --muted:  #57606A;
    --faint:  #EAEEF2;
    --red:    #CF222E;
    --amber:  #9A6700;
    --green:  #1A7F37;
    --blue:   #0969DA;
    --purple: #8250DF;
  }}
}}

html {{ scroll-behavior: smooth; }}

body {{
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 14px;
  line-height: 1.6;
}}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--faint); border-radius: 3px; }}

/* ── top nav ──────────────────────────────────────────────────── */
.topnav {{
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg);
  border-bottom: 1px solid var(--brd);
}}
.nav-inner {{
  max-width: 800px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  height: 48px;
}}
.nav-logo {{
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  flex-shrink: 0;
  margin-right: 20px;
  letter-spacing: -0.2px;
}}
.nav-links {{
  display: flex;
  gap: 2px;
  flex: 1;
}}
.nav-links a {{
  padding: 5px 10px;
  text-decoration: none;
  color: var(--muted);
  font-size: 13px;
  border-radius: 4px;
  transition: color 0.1s, background 0.1s;
}}
.nav-links a:hover {{ color: var(--text); background: var(--surf); }}
.health-badge {{
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}}
.health-num {{
  font-family: var(--mono);
  font-size: 18px;
  font-weight: 500;
  line-height: 1;
}}
.health-lbl {{
  font-size: 9px;
  color: var(--muted);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  line-height: 1;
}}
.health-bar {{
  width: 52px;
  height: 2px;
  background: var(--brd);
  border-radius: 1px;
  margin-top: 1px;
}}
.health-fill {{ height: 100%; border-radius: 1px; }}

/* ── main ─────────────────────────────────────────────────────── */
.main {{
  max-width: 800px;
  margin: 0 auto;
  padding: 52px 24px 100px;
}}

/* ── sections ─────────────────────────────────────────────────── */
.section {{ margin-bottom: 64px; }}
.section-hd {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}}
.eyebrow {{
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}}
.count-badge {{
  font-family: var(--mono);
  font-size: 10px;
  color: var(--muted);
  background: var(--surf);
  border: 1px solid var(--brd);
  padding: 2px 8px;
  border-radius: 2px;
}}

/* ── brief ────────────────────────────────────────────────────── */
.verdict {{
  font-size: 15px;
  line-height: 1.75;
  color: var(--text);
  margin-bottom: 24px;
}}
.verdict code {{
  font-family: var(--mono);
  font-size: 13px;
  background: var(--surf);
  border: 1px solid var(--brd);
  padding: 1px 5px;
  border-radius: 3px;
  color: var(--amber);
}}
.verdict strong {{ font-weight: 500; }}
.stat-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 28px;
  border-top: 1px solid var(--brd);
  padding-top: 20px;
}}
.stat {{ display: flex; align-items: baseline; gap: 5px; }}
.stat-n {{
  font-family: var(--mono);
  font-size: 15px;
  font-weight: 500;
}}
.stat-l {{ font-size: 12px; color: var(--muted); }}

/* ── rows (triage) ────────────────────────────────────────────── */
.row-list {{
  border: 1px solid var(--brd);
  border-radius: 4px;
  overflow: hidden;
}}
.row {{
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 14px;
  border-bottom: 1px solid var(--brd);
  text-decoration: none;
  color: var(--text);
  transition: background 0.1s;
}}
.row:last-child {{ border-bottom: none; }}
.row:hover {{ background: var(--surf); }}
.dot {{
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}}
.row-body {{ flex: 1; min-width: 0; }}
.row-title {{ font-size: 13px; display: block; }}
.row-detail {{
  font-size: 11px;
  color: var(--muted);
  font-family: var(--mono);
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}}
.row-end {{
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}}
.chev {{ color: var(--muted); font-size: 16px; line-height: 1; }}

/* ── chips ────────────────────────────────────────────────────── */
.chip {{
  font-size: 11px;
  padding: 2px 7px;
  border: 1px solid var(--brd);
  border-radius: 2px;
  color: var(--muted);
  white-space: nowrap;
  display: inline-block;
}}
.chip.mono {{ font-family: var(--mono); }}
.chip.red    {{ color: var(--red);   border-color: var(--red);   background: rgba(226,75,74,0.08);   }}
.chip.amber  {{ color: var(--amber); border-color: var(--amber); background: rgba(210,153,34,0.08);  }}
.chip.green  {{ color: var(--green); border-color: var(--green); background: rgba(63,185,80,0.08);   }}

/* ── file explorer ────────────────────────────────────────────── */
.files-toolbar {{
  display: flex;
  gap: 8px;
  margin-bottom: 1px;
}}
.search-input {{
  flex: 1;
  background: var(--surf);
  border: 1px solid var(--brd);
  color: var(--text);
  font-family: var(--font);
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 4px;
  outline: none;
}}
.search-input::placeholder {{ color: var(--muted); }}
.search-input:focus {{ border-color: var(--blue); }}
.filter-btn {{
  background: var(--surf);
  border: 1px solid var(--brd);
  color: var(--muted);
  font-family: var(--font);
  font-size: 12px;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.1s, border-color 0.1s;
}}
.filter-btn:hover {{ color: var(--text); }}
.filter-btn.active {{ color: var(--text); border-color: var(--text); }}
.file-list {{
  border: 1px solid var(--brd);
  border-radius: 4px;
  overflow: hidden;
}}
.file-row {{ border-bottom: 1px solid var(--brd); }}
.file-row:last-child {{ border-bottom: none; }}
.file-hd {{
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  color: var(--text);
  transition: background 0.1s;
}}
.file-hd:hover {{ background: var(--surf); }}
.file-name {{
  font-size: 13px;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: left;
}}
.file-cx {{
  font-size: 13px;
  font-weight: 500;
  flex-shrink: 0;
}}
.file-detail {{
  display: none;
  padding: 14px 14px 16px 31px;
  border-top: 1px solid var(--brd);
  background: var(--surf);
}}
.sym-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  margin-bottom: 12px;
}}
.sym-table th {{
  text-align: left;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  font-weight: 500;
  padding: 0 8px 8px 0;
  border-bottom: 1px solid var(--brd);
}}
.sym-table td {{
  padding: 7px 8px 7px 0;
  border-bottom: 1px solid var(--brd);
  color: var(--muted);
  vertical-align: top;
}}
.sym-table td:first-child {{ color: var(--text); }}
.sym-table tr:last-child td {{ border-bottom: none; }}
.trunc {{
  max-width: 280px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.pill-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}}

/* ── dep hubs ─────────────────────────────────────────────────── */
.dep-desc {{
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 16px;
  line-height: 1.6;
}}
.hub-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}}
.hub-card {{
  border: 1px solid var(--brd);
  padding: 12px;
  border-radius: 4px;
  text-decoration: none;
  display: block;
  transition: background 0.1s;
}}
.hub-card:hover {{ background: var(--surf); }}
.hub-name {{
  font-size: 12px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 3px;
}}
.hub-count {{ font-size: 11px; color: var(--muted); margin-bottom: 8px; }}
.hub-bar {{ height: 2px; background: var(--brd); border-radius: 1px; }}

/* ── dead code ────────────────────────────────────────────────── */
.callout {{
  font-size: 13px;
  color: var(--muted);
  padding: 12px 14px;
  border: 1px solid var(--brd);
  border-radius: 4px;
  line-height: 1.6;
  margin-bottom: 10px;
}}
.collapse-wrap {{ margin-bottom: 4px; }}
.collapse-btn {{
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--surf);
  border: 1px solid var(--brd);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: var(--muted);
  font-family: var(--font);
  transition: color 0.1s;
}}
.collapse-btn:hover {{ color: var(--text); }}
.dead-list {{
  display: none;
  border: 1px solid var(--brd);
  border-top: none;
  border-radius: 0 0 4px 4px;
}}
.dead-row {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-bottom: 1px solid var(--brd);
  font-size: 12px;
}}
.dead-row:last-child {{ border-bottom: none; }}

/* ── circular imports ─────────────────────────────────────────── */
.success-bar {{
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 13px;
  color: var(--green);
  background: rgba(63,185,80,0.06);
  border: 1px solid rgba(63,185,80,0.25);
}}
.cycle-list {{
  border: 1px solid var(--brd);
  border-radius: 4px;
  overflow: hidden;
}}
.cycle-row {{
  padding: 10px 14px;
  border-bottom: 1px solid var(--brd);
  font-size: 12px;
  color: var(--red);
}}
.cycle-row:last-child {{ border-bottom: none; }}

/* ── utilities ────────────────────────────────────────────────── */
.mono  {{ font-family: var(--mono); }}
.muted {{ color: var(--muted); }}
.small {{ font-size: 12px; }}
.empty {{
  font-size: 13px;
  color: var(--muted);
  padding: 16px;
  border: 1px solid var(--brd);
  border-radius: 4px;
}}
</style>
</head>
<body>

<header class="topnav">
  <div class="nav-inner">
    <span class="nav-logo">&#x2B21; Axiom</span>
    <nav class="nav-links">
      <a href="#brief">Brief</a>
      <a href="#triage">Triage</a>
      <a href="#files">Files</a>
      <a href="#dep-map">Dependencies</a>
      <a href="#dead-code">Dead code</a>
    </nav>
    <div class="health-badge">
      <span class="health-num" style="color:{h_color}">{health}</span>
      <span class="health-lbl">{h_label}</span>
      <div class="health-bar">
        <div class="health-fill" style="width:{health}%;background:{h_color}"></div>
      </div>
    </div>
  </div>
</header>

<main class="main">

<!-- BRIEF -->
<section class="section" id="brief">
  <div class="eyebrow" style="margin-bottom:14px">Brief &nbsp;&middot;&nbsp; <span style="font-weight:400;text-transform:none;letter-spacing:0">{project_name} &nbsp;&middot;&nbsp; {generated}</span></div>
  <p class="verdict">{brief}</p>
  <div class="stat-row">
    <div class="stat">
      <span class="stat-n">{n_files}</span>
      <span class="stat-l">Python files</span>
    </div>
    <div class="stat">
      <span class="stat-n">{total_fns}</span>
      <span class="stat-l">Functions</span>
    </div>
    <div class="stat">
      <span class="stat-n" style="color:{avg_cx_color}">{avg_cx}</span>
      <span class="stat-l">Avg complexity</span>
    </div>
    <div class="stat">
      <span class="stat-n" style="color:{smells_color}">{total_smells}</span>
      <span class="stat-l">Code smells</span>
    </div>
    <div class="stat">
      <span class="stat-n" style="color:{dead_color}">{real_dead_n}</span>
      <span class="stat-l">Dead functions</span>
    </div>
    <div class="stat">
      <span class="stat-n" style="color:{circles_color}">{len(circles)}</span>
      <span class="stat-l">Import cycles</span>
    </div>
  </div>
</section>

<!-- WHAT TO FIX -->
<section class="section" id="triage">
  <div class="section-hd">
    <span class="eyebrow">What to fix</span>
    <span class="count-badge">{n_findings} findings</span>
  </div>
  {triage_html}
</section>

<!-- FILES -->
<section class="section" id="files">
  <div class="section-hd">
    <span class="eyebrow">Files</span>
    <span class="count-badge">{n_files} files</span>
  </div>
  <div class="files-toolbar">
    <input class="search-input" type="text" id="search"
           placeholder="Search files&#8230;" oninput="filterFiles()" />
    <button class="filter-btn" id="risky-btn" onclick="toggleRisky()">Risky only</button>
  </div>
  <div class="file-list" id="file-list">
{files_html}
  </div>
</section>

<!-- DEPENDENCIES -->
<section class="section" id="dep-map">
  <div class="section-hd">
    <span class="eyebrow">Dependencies</span>
  </div>
  <p class="dep-desc">Files imported by many modules are hub files — a change here ripples
  across the whole system. Treat them like public APIs.</p>
  {dep_html}
</section>

<!-- DEAD CODE -->
<section class="section" id="dead-code">
  <div class="section-hd">
    <span class="eyebrow">Dead code</span>
    <span class="count-badge">{real_dead_n} symbols</span>
  </div>
  {dead_html}
</section>

<!-- CIRCULAR IMPORTS -->
<section class="section" id="circular">
  <div class="section-hd">
    <span class="eyebrow">Circular imports</span>
  </div>
  {circles_html}
</section>

</main>

<script>
function toggleFile(id) {{
  var det  = document.getElementById('det-'  + id);
  var chev = document.getElementById('chev-' + id);
  var open = det.style.display === 'block';
  det.style.display    = open ? 'none' : 'block';
  chev.style.transform = open ? ''     : 'rotate(90deg)';
}}

var riskyOnly = false;
function toggleRisky() {{
  riskyOnly = !riskyOnly;
  document.getElementById('risky-btn').classList.toggle('active', riskyOnly);
  filterFiles();
}}

function filterFiles() {{
  var q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.file-row').forEach(function(row) {{
    var nameMatch = !q || row.dataset.name.includes(q);
    var riskMatch = !riskyOnly || row.dataset.risk === 'risky';
    row.style.display = (nameMatch && riskMatch) ? '' : 'none';
  }});
}}

function toggleDead() {{
  var list = document.getElementById('dead-list');
  var chev = document.getElementById('dead-chev');
  var open = list.style.display === 'block';
  list.style.display   = open ? 'none' : 'block';
  chev.style.transform = open ? ''     : 'rotate(90deg)';
}}
</script>

</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)
