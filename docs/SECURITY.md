# Security Considerations

Axiom-Code processes arbitrary user-supplied codebases by parsing files, executing Python's `ast.parse()`, and writing output files. Each of these surfaces has attack vectors that must be understood and mitigated.

---

## 1. Arbitrary File Read via Path Traversal

### Risk: HIGH

`project_scanner.py` accepts a `root` path from user input (via the CLI `path` argument) and recursively reads every file under it with no restrictions:

```python
for path in root.rglob("*"):
    source = load_file(path)
```

If a user — or a script invoking Axiom programmatically — passes a path like `/`, `/etc`, or `~/.ssh`, the scanner will attempt to load and process every readable file on the system.

### Mitigations
- Resolve and validate the input path before scanning:

```python
def scan_project(root: Path) -> ProjectIndex:
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project path: {root}")
```

- Enforce that the resolved path stays within a configured allowed root (important for server/API deployments).
- Respect `.gitignore` rules — never scan files that a project explicitly excludes. Use a library like `gitignore-parser` or replicate the logic.
- Skip known sensitive directories explicitly:

```python
SKIP_DIRS = {".git", ".ssh", "node_modules", "__pycache__", ".env"}
if path.name in SKIP_DIRS:
    continue
```

---

## 2. AST Parsing of Malicious Input

### Risk: MEDIUM

`ast.parse()` in Python does not execute code. It is generally safe. However:

- **Deeply nested ASTs** can cause Python's recursion limit to be hit, crashing the process. A file with thousands of nested structures (e.g., `[[[[[...` repeated) can trigger a `RecursionError`.
- **Extremely large files** can cause `ast.parse()` to consume significant memory and CPU.
- **Malformed files** will raise `SyntaxError`, which is currently not caught in `symbol_table.py` or `call_graph.py`, causing the entire analysis run to crash rather than skipping the file.

### Mitigations

Wrap all `ast.parse()` calls in controlled exception handling:

```python
def safe_parse(source: str) -> Optional[ast.AST]:
    try:
        return ast.parse(source)
    except SyntaxError:
        logger.debug("Skipping file with syntax error")
        return None
    except RecursionError:
        logger.warning("Skipping deeply nested file (recursion limit hit)")
        return None
    except MemoryError:
        logger.warning("Skipping file: ran out of memory during parse")
        return None
```

Enforce the file size limit (currently configured but not implemented) before parsing.

---

## 3. Output Path Injection

### Risk: MEDIUM

The `--output` and `--json` CLI arguments are passed directly to file write operations with no validation:

```python
# analyze_cmd.py
write_markdown(explanations, args.output)
write_json(summary, args.json)
```

```python
# markdown_writer.py
with open(output_path, "w", encoding="utf-8") as f:
    f.write(...)
```

A path like `../../etc/cron.d/malicious` or `/home/user/.bashrc` would be written to without question. In automated pipelines where the output path is constructed programmatically, this is a genuine risk.

### Mitigations
- Validate output paths before writing:

```python
def safe_output_path(path_str: str, allowed_base: Path) -> Path:
    resolved = Path(path_str).resolve()
    if not str(resolved).startswith(str(allowed_base)):
        raise ValueError(f"Output path escapes allowed directory: {resolved}")
    return resolved
```

- For the CLI, at minimum check that the output path is a valid filename and not an absolute system path unless explicitly confirmed.

---

## 4. Sensitive File Exposure in Reports

### Risk: MEDIUM

The tool reads and indexes source files, then writes their contents (symbols, imports, docstrings) into output reports. If a project contains files with hardcoded secrets — API keys, passwords, private keys embedded in source comments or docstrings — those strings will be extracted and written into the Markdown or JSON report.

Example: A Python file containing:

```python
API_KEY = "sk-live-abc123..."  # prod key
```

The symbol `API_KEY` and surrounding context will appear in the generated report.

### Mitigations
- Add a secrets detection pass before report generation. Scan extracted strings against known secret patterns (AWS keys, GitHub tokens, private key headers):

```python
SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{32,}",           # OpenAI / Anthropic keys
    r"AKIA[0-9A-Z]{16}",               # AWS access key
    r"-----BEGIN (RSA|EC) PRIVATE KEY",
    r"ghp_[a-zA-Z0-9]{36}",            # GitHub personal access token
]
```

- Redact matched values before writing output.
- Document this risk clearly in the README so users understand that reports should not be committed to public repositories.

---

## 5. Uncontrolled Recursion in Deep Directory Trees

### Risk: LOW-MEDIUM

`root.rglob("*")` follows symlinks by default on some systems. A directory tree containing a symlink that points to a parent directory creates an infinite loop. Python's `Path.rglob` does not detect symlink cycles.

### Mitigation

```python
for path in root.rglob("*"):
    if path.is_symlink():
        logger.debug("Skipping symlink: %s", path)
        continue
    ...
```

Or use `os.walk()` with `followlinks=False` for explicit control.

---

## 6. Cache Directory Contains Sensitive Derived Data

### Risk: LOW

The `.axiom_cache` directory stores analysis artifacts keyed by content hash. If a project contains sensitive source code, the cached analysis results also contain sensitive derived information (symbol names, call graphs, docstrings). The cache directory:

- Is written to the project root (`.axiom_cache/`)
- Is not listed in any `.gitignore` template
- Has no access controls beyond the filesystem

### Mitigations
- Add `.axiom_cache/` to a generated `.gitignore` entry on first run.
- Document that the cache directory should not be committed or shared.
- Consider an option to store the cache outside the project directory (e.g., in `~/.cache/axiom/`).

---

## 7. No Input Sanitization in Markdown Output

### Risk: LOW (for current use, higher if used in web contexts)

`markdown_writer.py` writes file paths and function names directly into Markdown without escaping:

```python
lines.append(f"# {path}\n")
lines.append(f"## Function: {fn.name}")
```

If the output Markdown is ever rendered in a web context (e.g., a GitHub Pages site, a documentation platform, or an Electron app), a file path or function name containing Markdown control characters or HTML could inject content.

Example: A function named `<script>alert(1)</script>` in a source file would propagate directly into the report.

### Mitigation
Escape special characters in user-derived strings before writing them into structured output formats. This becomes critical if Axiom ever exposes a web interface or API.

---

## 8. Dependency Supply Chain

### Risk: LOW (currently)

`requirements.txt` pins no versions:

```
networkx
rich
```

Unpinned dependencies mean any `pip install` pulls the latest version, which could introduce breaking changes or, in a worst case, a compromised package version if a maintainer account is compromised.

### Mitigation
- Pin all dependencies to specific versions with hashes in production:

```
networkx==3.3
rich==13.7.1
```

- Use `pip-audit` to check for known CVEs in the dependency tree before releases.
