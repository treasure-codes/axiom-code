import ast
from typing import List, Optional

from axiom.core.models import CodeSymbol


class PythonASTParser(ast.NodeVisitor):
    def __init__(self) -> None:
        self.symbols: List[CodeSymbol] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
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

    # Treat async functions identically to sync functions
    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
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


def safe_parse(source: str) -> Optional[ast.AST]:
    """Parse Python source safely. Returns None on any parse error."""
    try:
        return ast.parse(source)
    except SyntaxError:
        return None
    except RecursionError:
        return None
    except MemoryError:
        return None
