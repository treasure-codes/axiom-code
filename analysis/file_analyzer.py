from axiom.parsing.symbol_table import extract_symbols
from axiom.parsing.dependency_graph import extract_imports
from axiom.analysis.call_graph import build_call_graph


def analyze_file(code_file):
    symbols = extract_symbols(code_file.source)
    imports = extract_imports(code_file.source)
    call_graph = build_call_graph(code_file.source)

    code_file.symbols = symbols
    code_file.imports = imports
    code_file.call_graph = call_graph

    return code_file
