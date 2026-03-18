# Architecture Improvements

Structural and design-level improvements to make Axiom-Code more robust, extensible, and correct. These are not bug fixes — they are architectural decisions that will determine how far this project can scale.

---

## 1. Separate the Analysis Data Model from the Raw Data Model

### Problem
`CodeFile` currently serves two roles: it's the raw ingestion container (path, source, language, hash) AND the post-analysis result container (complexity, call_graph, smells, priority). These concerns collide. Code that only needs raw file data gets dragged into knowing about analysis outputs.

### Recommended Fix
Split into two distinct models:

```python
# core/models.py — Raw ingestion output
@dataclass
class CodeFile:
    path: str
    language: str
    source: str
    symbols: List[CodeSymbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    hash: Optional[str] = None

# analysis/models.py — Post-analysis output
@dataclass
class AnalyzedFile:
    file: CodeFile                          # original raw data
    call_graph: Dict[str, Set[str]]
    complexity: int
    priority: Dict[str, float]
    smells: List[SmellResult]
```

The `file_analyzer.py` function signature changes from mutating `CodeFile` to returning `AnalyzedFile`:

```python
def analyze_file(code_file: CodeFile) -> AnalyzedFile:
    ...
    return AnalyzedFile(file=code_file, call_graph=..., ...)
```

This makes the pipeline immutable and each stage's inputs/outputs explicit.

---

## 2. Build a Cross-File Dependency Graph

### Problem
The current call graph is **intra-file only**. Each file gets its own isolated call graph. There is no model of how files depend on each other, which modules import which, or which functions are called across file boundaries.

### What to Build
A `ProjectGraph` that models the full project as a graph using `networkx` (already listed as a dependency — use it):

```python
import networkx as nx

@dataclass
class ProjectGraph:
    file_graph: nx.DiGraph     # nodes = files, edges = import dependencies
    symbol_graph: nx.DiGraph   # nodes = functions/classes, edges = calls (cross-file)
```

**Why this matters:**
- You can compute real PageRank-based importance scores instead of the current hand-wavy `inbound + outbound` formula
- You can detect circular imports
- You can identify entry points (nodes with no inbound edges) and dead code (nodes with no outbound or inbound edges)
- You can answer "what breaks if I delete this function?"

---

## 3. Replace the Fake Priority Score with Proper Graph Metrics

### Problem
The current scoring formula:

```python
def priority_score(complexity: int, importance: int) -> float:
    return round((0.6 * complexity) + (0.4 * importance), 2)
```

The 0.6/0.4 weights are invented. The "importance" metric is just node degree. This isn't analysis — it's a formula that feels like analysis.

### Recommended Fix
Once the `ProjectGraph` is built with `networkx`, replace this with real metrics:

```python
import networkx as nx

def compute_importance(symbol_graph: nx.DiGraph) -> Dict[str, float]:
    # PageRank: functions called by many other important functions score higher
    return nx.pagerank(symbol_graph)

def compute_betweenness(symbol_graph: nx.DiGraph) -> Dict[str, float]:
    # Betweenness: functions that are "bridges" in the call graph
    return nx.betweenness_centrality(symbol_graph)
```

These are interpretable, theoretically grounded, and already available in `networkx`.

---

## 4. Make the Analysis Pipeline Composable

### Problem
The pipeline in `orchestration/pipeline.py` is a hardcoded sequence. Adding a new analysis stage (e.g., type flow analysis, dead code detection) requires modifying the pipeline function itself.

### Recommended Fix
Define a `PipelineStage` protocol and compose the pipeline from stages:

```python
from typing import Protocol

class AnalysisStage(Protocol):
    def run(self, project: ProjectIndex) -> ProjectIndex:
        ...

class Pipeline:
    def __init__(self, stages: List[AnalysisStage]):
        self.stages = stages

    def run(self, path: str) -> ProjectIndex:
        project = scan_project(Path(path))
        for stage in self.stages:
            project = stage.run(project)
        return project
```

New stages can be added without touching existing code.

---

## 5. Replace Magic Number Smell Thresholds with Configuration

### Problem
Smell detection uses hardcoded thresholds:

```python
if score > 15:      # HighComplexitySmell
if len(...) > 10:   # GodFileSmell
```

These numbers are arbitrary and buried in implementation files. Different projects have different norms.

### Fix
Expose thresholds in `AxiomConfig`:

```python
@dataclass
class AxiomConfig:
    ...
    complexity_threshold: int = 15
    god_file_symbol_threshold: int = 10
```

And inject the config into smell detectors:

```python
class HighComplexitySmell(CodeSmell):
    def detect(self, code_file, config: AxiomConfig):
        if code_file.complexity > config.complexity_threshold:
            ...
```

---

## 6. Implement a Real Caching Layer

### Problem
`AxiomConfig` has `enable_caching: bool = True` and `config.py` creates a `.axiom_cache` directory — but there is **no caching implementation anywhere**. The cache directory is created and then never used.

### What to Build
A file-level cache keyed by content hash:

```python
# core/cache.py
import json
from pathlib import Path
from axiom.core.models import AnalyzedFile

class AnalysisCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir

    def _path(self, file_hash: str) -> Path:
        return self.cache_dir / f"{file_hash}.json"

    def get(self, file_hash: str) -> Optional[AnalyzedFile]:
        p = self._path(file_hash)
        if p.exists():
            return AnalyzedFile.from_dict(json.loads(p.read_text()))
        return None

    def put(self, file_hash: str, result: AnalyzedFile) -> None:
        self._path(file_hash).write_text(
            json.dumps(result.to_dict(), indent=2)
        )
```

This would make re-analysis of unchanged files nearly instantaneous.

---

## 7. Expand the Parser Infrastructure for Multi-Language Support

### Problem
`language_detector.py` already maps `.java`, `.js`, `.ts` to language names — but there is exactly one parser implementation (`PythonASTParser`) and it is Python-specific. The multi-language infrastructure is incomplete scaffolding.

### Recommended Architecture
Define a `LanguageParser` protocol and implement per-language:

```python
# parsing/base.py
from typing import Protocol

class LanguageParser(Protocol):
    def extract_symbols(self, source: str) -> List[CodeSymbol]: ...
    def extract_imports(self, source: str) -> List[str]: ...
    def build_call_graph(self, source: str) -> Dict[str, Set[str]]: ...

# parsing/registry.py
PARSERS: Dict[str, LanguageParser] = {
    "python": PythonParser(),
}

def get_parser(language: str) -> Optional[LanguageParser]:
    return PARSERS.get(language)
```

`file_analyzer.py` selects the correct parser based on `code_file.language` instead of assuming Python.

---

## 8. Add Structured SmellResult Instead of Raw Dicts

### Problem
Smell detection returns plain Python dicts:

```python
return {
    "smell": self.name,
    "score": score,
    "message": "Consider refactoring this file."
}
```

Dicts have no type guarantees. Adding a new field to one smell but not another creates inconsistency that only breaks at runtime.

### Fix
Define a proper dataclass:

```python
@dataclass
class SmellResult:
    name: str
    severity: str          # "low", "medium", "high"
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## 9. Decouple the Explanation Engine from the Analysis Engine

### Problem
`explanation_engine.py` only works on `call_graph` data, which means it is completely dependent on `file_analyzer.py` having already been run. There's no explicit contract making this dependency clear.

### Fix
The explanation engine should accept a typed `AnalyzedFile` as input, making the dependency explicit in the type signature:

```python
def explain_file(analyzed: AnalyzedFile) -> FileExplanation:
    ...
```

Not a `CodeFile` — an `AnalyzedFile`. This way, if you pass an un-analyzed file, the type checker catches it before runtime.

---

## 10. Add a Proper Entry Point in `pyproject.toml`

### Problem
There's no `[project.scripts]` entry in `pyproject.toml`. Running the tool after `pip install` requires knowing to call `python -m axiom.cli.main`. New users have no way to discover this.

### Fix

```toml
[project.scripts]
axiom = "axiom.cli.main:main"
```

After `pip install -e .`, running `axiom analyze .` should just work.
