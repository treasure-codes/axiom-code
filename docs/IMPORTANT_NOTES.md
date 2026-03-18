# Important Notes — Things to Add, Improve, and Work On

This document covers gaps in completeness, missing features that are partially scaffolded but unfinished, and important quality-of-life work that will determine whether this project is usable in practice.

---

## 1. There Are Zero Tests — This Is the Highest Priority Item After the Import Fix

The entire project has no test files. Not a single one. Every module that does real work — AST parsing, call graph construction, complexity scoring, smell detection, output writing — is completely untested.

### What to Build First

A `tests/` directory with `pytest`:

```
tests/
├── conftest.py                  # shared fixtures (sample CodeFile, sample source strings)
├── test_ast_parser.py           # verify symbol extraction from Python source
├── test_call_graph.py           # verify intra-file call relationships
├── test_complexity.py           # verify complexity scores for known inputs
├── test_smells.py               # verify thresholds trigger and don't trigger
├── test_scoring.py              # verify priority score formula
├── test_scanner.py              # verify file discovery and filtering
├── test_pipeline.py             # integration test: full run on a small fixture project
└── test_output_writers.py       # verify markdown and JSON output format
```

### Minimum Acceptable Coverage Target
- All metrics functions: 100% (they are pure functions — no excuse not to)
- All smell detectors: 100%
- Pipeline integration: at least one end-to-end test on a real fixture directory

### Quick Start
```bash
pip install pytest pytest-cov
pytest tests/ --cov=axiom --cov-report=term-missing
```

---

## 2. The Call Graph is Fundamentally Incomplete

The current `CallGraphBuilder` only captures this pattern:

```python
def foo():
    bar()   # tracked: ast.Name node
```

It misses all of these, which make up the majority of real Python code:

```python
def foo():
    self.bar()          # method call — ast.Attribute, not ast.Name
    obj.helper()        # attribute call — missed
    module.function()   # imported call — missed
    fn = get_fn()
    fn()                # dynamic call — missed
    [x.process() for x in items]  # call in comprehension — partially missed
```

Until this is fixed, call graphs generated for real-world Python code will be sparse and misleading. The importance scores derived from these graphs will be inaccurate.

### What to Fix in `analysis/call_graph.py`

```python
def visit_Call(self, node):
    if self.current_function:
        if isinstance(node.func, ast.Name):
            self.graph[self.current_function].add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # e.g., self.method() or obj.method()
            self.graph[self.current_function].add(node.func.attr)
    self.generic_visit(node)
```

Also handle `ast.AsyncFunctionDef` — async functions are currently not visited at all.

---

## 3. The Explanation Engine Generates Useless Output

Every function explanation looks like this:

```
purpose: "Function extracted from source code."
summary: "foo calls 3 other functions."
```

This is not an explanation. It adds zero value over looking at the source code. Users running `axiom explain` will immediately dismiss the output as noise.

### What Needs to Happen

**Short-term (no AI required):**
- Use the docstring if one exists — this is already extracted in `CodeSymbol.docstring`, it's just not being used in the explanation engine
- Describe what the function calls by name: `"foo calls bar, baz, and qux"`
- Note the function's position in the file (entry point, utility, internal helper)
- Flag functions with high complexity scores or that appear in smell results

**Medium-term (with AI):**
- The `context_builder.py` infrastructure already builds LLM-ready context objects. Wire these up to an optional LLM call (Claude API, OpenAI, local model via Ollama) when `enable_llm: True` is set in config.
- The deterministic explanation should be the fallback, not the primary path.

---

## 4. The `--summary` Flag Doesn't Work Correctly with `--output`

Looking at `analyze_cmd.py`:

```python
if args.summary:
    summary = summarize_project(project)
    if args.json:
        write_json(summary, args.json)
    else:
        print(summary)
    return   # exits early — no markdown report written
```

If the user runs `axiom analyze . --summary --output report.md`, they expect both a summary and a markdown report. Instead, the `--summary` flag causes early return and `report.md` is never written.

The flag combination logic needs to be rethought. `--summary` should be an addition to the output, not a replacement for it.

---

## 5. No `.gitignore` Awareness

The project scanner does not respect `.gitignore`. Running `axiom analyze .` on a Python project will attempt to analyze:

- `node_modules/` (if it exists)
- `__pycache__/` directories
- `.venv/` or `venv/` virtual environments
- Build artifacts in `dist/`, `build/`, `*.egg-info/`
- Test fixture files that shouldn't be treated as production code

This produces noisy output and wastes significant time. At minimum, the scanner should skip these directories unconditionally:

```python
ALWAYS_SKIP = {
    "__pycache__", ".git", ".venv", "venv", "env",
    "node_modules", "dist", "build", ".tox", ".mypy_cache",
    ".pytest_cache", "*.egg-info"
}
```

Longer-term, parse `.gitignore` using `pathspec` or `gitignore-parser`.

---

## 6. No CLI Help or Error Messages for Bad Input

Running `axiom analyze` with no path argument results in an argparse error, not a helpful message. Running `axiom analyze /nonexistent/path` results in an unhandled exception deep in `rglob()`, not a clean error.

Every CLI entry point needs input validation with human-readable errors before any work begins:

```python
def analyze_command(args):
    path = Path(args.path)
    if not path.exists():
        print(f"Error: path does not exist: {path}", file=sys.stderr)
        sys.exit(1)
    if not path.is_dir():
        print(f"Error: path is not a directory: {path}", file=sys.stderr)
        sys.exit(1)
    ...
```

---

## 7. No Progress Feedback for Large Projects

Analyzing a large repository (hundreds of files) gives the user no feedback — no progress bar, no file count, no indication anything is happening. For a CLI tool, this leads users to assume it's hung.

Use `rich` (already listed as a dependency) for a progress bar:

```python
from rich.progress import track

for path in track(paths, description="Analyzing..."):
    analyze_file(code_file)
```

---

## 8. `pyproject.toml` is Essentially Empty

The current `pyproject.toml` is missing most of what a real Python project needs:

```toml
[project]
name = "axiom-code"
version = "0.1.0"
description = "Autonomous Semantic Analysis & Interpretability Engine"
readme = "README.md"
requires-python = ">=3.10"
dependencies = []   # ← empty, but requirements.txt has deps
```

What it needs:

```toml
[project]
name = "axiom-code"
version = "0.1.0"
description = "Autonomous Semantic Analysis & Interpretability Engine"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "networkx>=3.0",
    "rich>=13.0",
]

[project.scripts]
axiom = "axiom.cli.main:main"   # ← makes `axiom` command available after install

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
    "mypy",
    "ruff",
]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.mypy]
python_version = "3.10"
strict = true
```

---

## 9. The Caching System is Advertised but Non-Existent

The README and config both reference caching as a feature. The `.axiom_cache` directory is created. But there is zero caching logic anywhere in the codebase. Re-running analysis on the same project re-parses every file from scratch every time.

Until caching is implemented, the `enable_caching: bool = True` config flag is misleading. Either implement it or remove the setting and the cache directory creation.

---

## 10. No Version Command

```bash
axiom --version
```

Should print the version from `__init__.py`. This is a one-line addition to `cli/main.py`:

```python
parser.add_argument("--version", action="version", version=f"axiom {__version__}")
```

---

## 11. Language Support is Misleading

`language_detector.py` maps `.java`, `.js`, `.ts` to language names. The README implies multi-language support is planned. But if you run Axiom on a TypeScript or Java project, the scanner will detect the files, load them, and then `file_analyzer.py` will call `extract_symbols()` which calls `ast.parse()` — a Python-only function — on the TypeScript source. This will raise a `SyntaxError` on every non-Python file.

Until parsers exist for those languages, `language_detector.py` should only return `"python"` for `.py` files, and silently skip everything else. Or the unsupported language entries should be removed from the map entirely to avoid false promises.

---

## 12. Smell Detection Has No Severity Levels

Both current smells (`HighComplexitySmell`, `GodFileSmell`) return a flat dict with no severity field. All smells look equally important in the output. A function with complexity 16 (just above threshold) is indistinguishable from one with complexity 200.

Add severity tiers:

```
complexity 16-25   → low
complexity 26-50   → medium
complexity 51+     → high / critical
```

This makes the output actionable instead of binary.

---

## 13. No Changelog or Release Tracking

There is no `CHANGELOG.md`. As this project evolves, there is no record of what changed between versions. Before any public release or team handoff, a changelog should be established and updated with each meaningful change.
