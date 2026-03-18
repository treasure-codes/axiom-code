import ast
from collections import defaultdict
from typing import Dict, Set

from axiom.parsing.ast_parser import safe_parse


class CallGraphBuilder(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_function: str | None = None
        self.graph: Dict[str, Set[str]] = defaultdict(set)

    def _enter_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        prev = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev

    visit_FunctionDef = _enter_function
    visit_AsyncFunctionDef = _enter_function

    def visit_Call(self, node: ast.Call) -> None:
        if self.current_function:
            if isinstance(node.func, ast.Name):
                # direct call: bar()
                self.graph[self.current_function].add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # method/attribute call: obj.method() or self.helper()
                self.graph[self.current_function].add(node.func.attr)
        self.generic_visit(node)


def build_call_graph(source: str) -> Dict[str, Set[str]]:
    tree = safe_parse(source)
    if tree is None:
        return {}
    builder = CallGraphBuilder()
    builder.visit(tree)
    return dict(builder.graph)
