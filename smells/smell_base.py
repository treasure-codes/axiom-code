from abc import ABC, abstractmethod


class CodeSmell(ABC):
    name: str
    description: str

    @abstractmethod
    def detect(self, code_file):
        pass
