# Fixes Required

Critical bugs, broken imports, logic errors, and anti-patterns that must be resolved before the tool can function correctly.

---

## CRITICAL — Tool is Currently Non-Functional

### 1. Broken Import in `orchestration/pipeline.py`

**File:** `orchestration/pipeline.py`, line 1
**Severity:** Fatal — the entire tool crashes on startup

```python
# BROKEN (module does not exist)
from axiom.parsing.project_indexer import index_project

# CORRECT
from axiom.core.project_scanner import scan_project
```

Also update the call on line 7:
```python
# BROKEN
project = index_project(path)

# CORRECT
project = scan_project(Path(path))
```

This is the single most important fix. Nothing in the tool executes until this is resolved.

---

## HIGH — Logic Errors and Anti-Patterns

### 2. Undeclared Attribute Injection on Dataclass (`analysis/file_analyzer.py`)

`CodeFile` is a typed dataclass with declared fields. `file_analyzer.py` dynamically injects new attributes at runtime that are not declared in the class definition:

```python
code_file.call_graph = build_call_graph(...)   # not in CodeFile
code_file.complexity = compute_complexity(...)  # not in CodeFile
code_file.priority = {...}                      # not in CodeFile
code_file.smells = []                           # not in CodeFile
```

**Problem:** This bypasses type checking entirely. Mypy and Pyright will not catch misuse of these fields. Any downstream code accessing `code_file.complexity` is relying on a runtime attribute that may or may not exist depending on whether `analyze_file()` has been called.

**Fix:** Declare all analysis-phase fields in `core/models.py`:

```python
@dataclass
class CodeFile:
    path: str
    language: str
    source: str
    symbols: List[CodeSymbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    hash: Optional[str] = None
    # Analysis phase fields
    call_graph: Dict[str, Set[str]] = field(default_factory=dict)
    complexity: int = 0
    priority: Dict[str, float] = field(default_factory=dict)
    smells: List[Dict] = field(default_factory=list)
```

---

### 3. Double AST Parse in Smell Detection (`smells/complexity_smells.py`)

`file_analyzer.py` already computes complexity and stores it on `code_file.complexity`. But `HighComplexitySmell.detect()` ignores that value and re-parses the source from scratch:

```python
# In file_analyzer.py
code_file.complexity = compute_complexity(code_file.source)  # parse #1

# In complexity_smells.py
def detect(self, code_file):
    score = compute_complexity(code_file.source)  # parse #2 — redundant
```

**Fix:** Use the already-computed value:

```python
def detect(self, code_file):
    score = getattr(code_file, "complexity", 0)
    if score > 15:
        ...
```

---

### 4. `symbol_table.py` — Two Bugs on One Line

**File:** `parsing/symbol_table.py`

```python
# Current broken code
def extract_symbols(source: str):
    parser = PythonASTParser()
    tree = parser.visit(__import__("ast").parse(source))  # Bug 1 + Bug 2
    return parser.symbols
```

**Bug 1:** `__import__("ast")` is a runtime hack. `import ast` was forgotten at the top of the file.
**Bug 2:** `ast.NodeVisitor.visit()` returns `None`. Assigning it to `tree` serves no purpose and is misleading.

**Fix:**

```python
import ast
from axiom.parsing.ast_parser import PythonASTParser

def extract_symbols(source: str):
    parser = PythonASTParser()
    parser.visit(ast.parse(source))
    return parser.symbols
```

---

### 5. Namespace Inconsistency — `logging_config.py`

**File:** `logging_config.py`, line 2

```python
# BROKEN — uses axiom_code namespace, everything else uses axiom
from axiom_code.config import CONFIG

# CORRECT
from axiom.config import CONFIG
```

This will raise an `ImportError` when the package is installed under the `axiom` name.

---

### 6. `config.py` Creates Directories at Import Time

```python
# This runs the moment config.py is imported — even in tests
CACHE_DIR.mkdir(exist_ok=True)
ARTIFACT_DIR.mkdir(exist_ok=True)
```

**Problem:** Importing any module that transitively imports `config.py` will silently create directories in whatever the current working directory is. This pollutes test environments and makes the tool behave unpredictably when imported as a library.

**Fix:** Move directory creation into an explicit initialization function called from `main()`, not at module level.

```python
def initialize_dirs():
    CACHE_DIR.mkdir(exist_ok=True)
    ARTIFACT_DIR.mkdir(exist_ok=True)
```

---

## MEDIUM — Silent Failures and Missing Validation

### 7. Broad Exception Swallowing in `core/file_loader.py`

```python
def load_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None  # All errors silently disappear
```

Permission errors, binary files, encoding errors, and disk errors all return `None` with no log, no warning, no indication to the user that a file was skipped.

**Fix:** At minimum, log the specific failure:

```python
import logging
logger = logging.getLogger(__name__)

def load_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logger.debug("Skipping binary/non-UTF-8 file: %s", path)
        return None
    except PermissionError:
        logger.warning("Permission denied reading file: %s", path)
        return None
    except OSError as e:
        logger.warning("Could not read %s: %s", path, e)
        return None
```

---

### 8. `analyze_command` Silently Outputs Nothing on the Default Path

```python
def analyze_command(args):
    ...
    if args.output:
        write_markdown(explanations, args.output)
    else:
        print("Analysis complete.")  # Tells the user nothing
```

If `--output` is not provided, the user gets the string `"Analysis complete."` — no data, no summary, no feedback on what was found. This makes the default execution mode useless.

**Fix:** Print a basic summary to stdout when no output file is specified.

---

### 9. `cli/main.py` Uses Wrong Import Namespace

```python
# Current
from axiom.cli.analyze_cmd import analyze_command
from axiom.cli.explain_cmd import explain_command
```

Verify these match the actual installed package name. If the project is installed as `axiom-code`, imports may need to be `axiom_code.cli.*`. This must be confirmed against `pyproject.toml` once the package name and module name are aligned.

---

### 10. `project_scanner.py` Has No Size Limit Check

`AxiomConfig` defines `max_file_size_kb: int = 500` but `scan_project()` never checks file size before loading. Large files (generated code, minified JS, data files) will be loaded entirely into memory.

**Fix:**

```python
MAX_BYTES = CONFIG.max_file_size_kb * 1024
if path.stat().st_size > MAX_BYTES:
    logger.debug("Skipping oversized file: %s", path)
    continue
```

---

## LOW — Dead Code and Redundancy

### 11. Duplicate Utility Functions

Two pairs of identical functions exist across different files:

| Function | File 1 | File 2 |
|---|---|---|
| Read file safely | `utils.py::read_file_safe()` | `core/file_loader.py::load_file()` |
| Hash a string | `utils.py::hash_content()` | `utils/hashing.py::hash_source()` |

Pick one location for each and delete the duplicate. `core/file_loader.py` and `utils/hashing.py` are the more purposeful locations.

---

### 12. `requirements.txt` vs `pyproject.toml` Mismatch

`requirements.txt` lists `networkx` and `rich`. `pyproject.toml` lists no dependencies. These must be consistent. Pick one source of truth (prefer `pyproject.toml`) and keep them in sync.

---

### 13. `utils/logger.py` and `logging_config.py` Both Set Up Logging

Two separate modules configure the logging system with slightly different formats and approaches. One should be deleted and all logging setup should go through a single module.
