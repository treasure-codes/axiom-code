from dataclasses import dataclass, field
from typing import List


@dataclass
class FunctionExplanation:
    name: str
    purpose: str        # docstring if available, otherwise inferred
    calls: List[str]
    summary: str        # human-readable one-liner


@dataclass
class FileExplanation:
    path: str
    overview: str
    functions: List[FunctionExplanation]
    dependencies: List[str]
    smells: List[str] = field(default_factory=list)
