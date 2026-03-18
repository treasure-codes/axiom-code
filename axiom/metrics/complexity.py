import ast

from axiom.parsing.ast_parser import safe_parse


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.score = 1

    def visit_If(self, node: ast.If) -> None:
        self.score += 1
        # Each elif/else branch adds complexity
        if node.orelse:
            self.score += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.score += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.score += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.score += len(node.handlers)
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # each `and`/`or` adds a branch
        self.score += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.score += 1
        self.generic_visit(node)


def compute_complexity(source: str) -> int:
    tree = safe_parse(source)
    if tree is None:
        return 0
    visitor = ComplexityVisitor()
    visitor.visit(tree)
    return visitor.score
