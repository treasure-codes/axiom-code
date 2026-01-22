from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class CodeSymbol:
    name: str
    symbol_type: str  # function, class, variable, import
    lineno: int
    end_lineno: Optional[int] = None
    docstring: Optional[str] = None


@dataclass
class CodeFile:
    path: str
    language: str
    source: str
    symbols: List[CodeSymbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    hash: Optional[str] = None


@dataclass
class ProjectIndex:
    files: Dict[str, CodeFile] = field(default_factory=dict)
