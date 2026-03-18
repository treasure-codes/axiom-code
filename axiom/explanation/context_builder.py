from typing import Any, Dict

from axiom.core.models import CodeFile


def build_function_context(code_file: CodeFile, function_name: str) -> Dict[str, Any]:
    symbol = next(
        (s for s in code_file.symbols if s.name == function_name), None
    )
    calls = list(code_file.call_graph.get(function_name, set()))
    return {
        "function": function_name,
        "docstring": symbol.docstring if symbol else None,
        "lineno": symbol.lineno if symbol else None,
        "calls": calls,
        "file_path": code_file.path,
        "complexity": code_file.complexity,
    }


def build_file_context(code_file: CodeFile) -> Dict[str, Any]:
    return {
        "path": code_file.path,
        "language": code_file.language,
        "symbols": [s.name for s in code_file.symbols],
        "imports": code_file.imports,
        "call_graph": {k: list(v) for k, v in code_file.call_graph.items()},
        "complexity": code_file.complexity,
        "smells": [s.name for s in code_file.smells],
    }
