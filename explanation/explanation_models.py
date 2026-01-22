from dataclasses import dataclass
from typing import List, Dict


@dataclass
class FunctionExplanation:
    name: str
    purpose: str
    calls: List[str]
    summary: str


@dataclass
class FileExplanation:
    path: str
    overview: str
    functions: List[FunctionExplanation]
    dependencies: List[str]
