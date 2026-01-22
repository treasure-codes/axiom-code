def build_function_context(code_file, function_name):
    symbol = next(
        (s for s in code_file.symbols if s.name == function_name),
        None
    )

    calls = code_file.call_graph.get(function_name, [])

    context = {
        "function": function_name,
        "docstring": symbol.docstring if symbol else None,
        "calls": list(calls),
        "file_path": code_file.path,
    }

    return context


def build_file_context(code_file):
    return {
        "path": code_file.path,
        "symbols": [s.name for s in code_file.symbols],
        "imports": code_file.imports,
        "call_graph": code_file.call_graph,
    }
