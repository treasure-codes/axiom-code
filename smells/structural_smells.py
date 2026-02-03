from axiom.smells.smell_base import CodeSmell


class GodFileSmell(CodeSmell):
    name = "God File"
    description = "File contains too many functions."

    def detect(self, code_file):
        if len(code_file.symbols) > 10:
            return {
                "smell": self.name,
                "count": len(code_file.symbols),
                "message": "Consider splitting this file."
            }
        return None
