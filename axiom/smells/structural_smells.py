from typing import Optional

from axiom.config import CONFIG
from axiom.core.models import CodeFile, SmellResult
from axiom.smells.smell_base import CodeSmell


def _god_file_severity(count: int, threshold: int) -> str:
    excess = count - threshold
    if excess >= 20:
        return "high"
    if excess >= 10:
        return "medium"
    return "low"


class GodFileSmell(CodeSmell):
    name = "God File"
    description = "File contains too many symbols (functions/classes)."

    def detect(self, code_file: CodeFile) -> Optional[SmellResult]:
        count = len(code_file.symbols)
        threshold = CONFIG.god_file_symbol_threshold
        if count <= threshold:
            return None
        return SmellResult(
            name=self.name,
            severity=_god_file_severity(count, threshold),
            message=(
                f"File defines {count} symbols (threshold: {threshold}). "
                "Consider splitting into focused modules."
            ),
            metadata={"symbol_count": count, "threshold": threshold},
        )
