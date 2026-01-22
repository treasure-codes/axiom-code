import ast
from axiom.core.models import CodeSymbol


class PythonASTParser(ast.NodeVisitor):
    def __init__(self):
        self.symbols = []

    def visit_FunctionDef(self, node):
        self.symbols.append(
            CodeSymbol(
                name=node.name,
                symbol_type="function",
                lineno=node.lineno,
                end_lineno=node.end_lineno,
                docstring=ast.get_docstring(node),
            )
        )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.symbols.append(
            CodeSymbol(
                name=node.name,
                symbol_type="class",
                lineno=node.lineno,
                end_lineno=node.end_lineno,
                docstring=ast.get_docstring(node),
            )
        )
        self.generic_visit(node)
