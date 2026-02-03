import ast


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.score = 1

    def visit_If(self, node):
        self.score += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.score += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.score += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        self.score += len(node.handlers)
        self.generic_visit(node)


def compute_complexity(source: str) -> int:
    tree = ast.parse(source)
    visitor = ComplexityVisitor()
    visitor.visit(tree)
    return visitor.score
