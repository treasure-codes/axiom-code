from abc import ABC, abstractmethod
from typing import Optional

from axiom.core.models import CodeFile, SmellResult


class CodeSmell(ABC):
    name: str
    description: str

    @abstractmethod
    def detect(self, code_file: CodeFile) -> Optional[SmellResult]:
        pass
