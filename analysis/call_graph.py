import ast
from collections import defaultdict


class CallGraphBuilder(ast.NodeVisitor):
    def __init__(self):
        self.current_function = None
        self.graph = defaultdict(set)

    def visit_FunctionDef(self, node):
        prev = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev

    def visit_Call(self, node):
        if self.current_function and isinstance(node.func, ast.Name):
            self.graph[self.current_function].add(node.func.id)
        self.generic_visit(node)


def build_call_graph(source: str):
    tree = ast.parse(source)
    builder = CallGraphBuilder()
    builder.visit(tree)
    return dict(builder.graph)
