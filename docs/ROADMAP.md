# Axiom-Code Roadmap

Features planned for the next phase of development. Focus is on visual output, richer analysis, and a proper HTML report that's actually shareable.

---

## Phase 1 — Visual Output (Current Sprint)

### 1. HTML Report with Embedded UI
**Goal:** Replace the flat markdown report with a self-contained HTML page you can open in any browser.

**What it includes:**
- Summary dashboard at the top (total files, avg complexity, smell count)
- Complexity bar chart (Chart.js — no install needed, loaded from CDN)
- Per-file cards with collapsible sections
- Syntax-highlighted function lists
- Smell badges with severity colors (green / yellow / red)
- Embedded Mermaid diagrams (dependency graph + call graph per file)

**How to use:**
```bash
axiom analyze . --html report.html
```

---

### 2. Dependency Graph (Mermaid)
**Goal:** Visual map of which files import which — rendered as a proper diagram.

**What it looks like:**
```
pipeline.py --> project_scanner.py
pipeline.py --> project_analyzer.py
project_analyzer.py --> file_analyzer.py
file_analyzer.py --> complexity.py
file_analyzer.py --> call_graph.py
```

Renders as a flowchart diagram inside the HTML report and in any Markdown viewer that supports Mermaid (GitHub, Notion, Obsidian).

---

### 3. Call Graph Diagram Per File
**Goal:** For each file, show a visual of which functions call which other functions.

Rendered as a Mermaid flowchart inside the file's card in the HTML report.

---

### 4. Complexity Heatmap / Bar Chart
**Goal:** Visual overview of complexity across the whole project.

- Bar chart: files ranked by complexity score, colored by severity
- Makes it immediately obvious which files need attention without reading anything

---

## Phase 2 — Smarter Analysis

### 5. Dead Code Detection
**Goal:** Find functions that exist but are never called by anything in the project.

**How it works:** Any function with zero inbound edges in the call graph is a dead code candidate.

**Output:** Listed in the HTML report under a "Dead Code" section with file + line number.

---

### 6. Circular Import Detection
**Goal:** Find import cycles before they cause runtime errors.

**How it works:** Build a directed graph of imports, run cycle detection (DFS). Report any cycles found.

**Output:** Shown as a warning in the HTML report with the full cycle path highlighted.

---

### 7. Change Impact Analysis
**Goal:** "If I change this function, what else could break?"

Given a function name, trace all callers up the call graph and list everything that depends on it.

```bash
axiom impact . --function scan_project
```

---

## Phase 3 — Developer Experience

### 8. Watch Mode
**Goal:** Re-run analysis automatically when files change.

```bash
axiom analyze . --watch --html report.html
```

Opens the HTML report in a browser and refreshes it live as you edit code.

### 9. `.axiomignore` File
**Goal:** Let projects define which paths to skip (like `.gitignore`).

```
tests/
migrations/
vendor/
```

### 10. Config File Support
**Goal:** Store project-specific settings in `axiom.toml` at the project root.

```toml
[analysis]
complexity_threshold = 20
god_file_threshold = 15

[output]
default_format = "html"
```

---

## Tech Stack for Visuals

| Feature | How |
|---|---|
| HTML report | Pure Python string generation, no template engine needed |
| Charts | Chart.js via CDN (no Python dep) |
| Diagrams | Mermaid.js via CDN (no Python dep) |
| Styling | Inline CSS, dark theme |
| Graphs | `networkx` for analysis, Mermaid for rendering |

No heavy dependencies. The HTML file is fully self-contained — open it offline, share it, commit it.
