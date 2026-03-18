from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class CodeSymbol:
    name: str
    symbol_type: str  # "function", "class"
    lineno: int
    end_lineno: Optional[int] = None
    docstring: Optional[str] = None


@dataclass
class SmellResult:
    name: str
    severity: str  # "low", "medium", "high"
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeFile:
    path: str
    language: str
    source: str
    # Populated by scanner
    symbols: List[CodeSymbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    hash: Optional[str] = None
    # Populated by analysis phase
    call_graph: Dict[str, Set[str]] = field(default_factory=dict)
    complexity: int = 0
    priority: Dict[str, float] = field(default_factory=dict)
    smells: List[SmellResult] = field(default_factory=list)


@dataclass
class ProjectIndex:
    files: Dict[str, CodeFile] = field(default_factory=dict)
