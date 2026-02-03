from axiom.smells.smell_base import CodeSmell
from axiom.metrics.complexity import compute_complexity


class HighComplexitySmell(CodeSmell):
    name = "High Complexity"
    description = "File has high cyclomatic complexity."

    def detect(self, code_file):
        score = compute_complexity(code_file.source)
        if score > 15:
            return {
                "smell": self.name,
                "score": score,
                "message": "Consider refactoring this file."
            }
        return None
