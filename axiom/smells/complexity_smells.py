from typing import Optional

from axiom.config import CONFIG
from axiom.core.models import CodeFile, SmellResult
from axiom.smells.smell_base import CodeSmell


def _complexity_severity(score: int, threshold: int) -> str:
    excess = score - threshold
    if excess >= 35:
        return "high"
    if excess >= 15:
        return "medium"
    return "low"


class HighComplexitySmell(CodeSmell):
    name = "High Complexity"
    description = "File has high cyclomatic complexity."

    def detect(self, code_file: CodeFile) -> Optional[SmellResult]:
        # Use the already-computed complexity — do NOT re-parse the source
        score = code_file.complexity
        threshold = CONFIG.complexity_threshold
        if score <= threshold:
            return None
        return SmellResult(
            name=self.name,
            severity=_complexity_severity(score, threshold),
            message=(
                f"Cyclomatic complexity is {score} (threshold: {threshold}). "
                "Consider breaking this file into smaller units."
            ),
            metadata={"score": score, "threshold": threshold},
        )
