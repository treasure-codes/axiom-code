from axiom.parsing.ast_parser import PythonASTParser


def extract_symbols(source: str):
    parser = PythonASTParser()
    tree = parser.visit(__import__("ast").parse(source))
    return parser.symbols
