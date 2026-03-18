from typing import List

from axiom.parsing.ast_parser import safe_parse
import ast


def extract_imports(source: str) -> List[str]:
    tree = safe_parse(source)
    if tree is None:
        return []

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    return sorted(imports)
