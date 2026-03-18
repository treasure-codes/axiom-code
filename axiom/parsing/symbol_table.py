from typing import List

from axiom.core.models import CodeSymbol
from axiom.parsing.ast_parser import PythonASTParser, safe_parse


def extract_symbols(source: str) -> List[CodeSymbol]:
    tree = safe_parse(source)
    if tree is None:
        return []
    parser = PythonASTParser()
    parser.visit(tree)
    return parser.symbols
