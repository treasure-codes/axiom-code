from axiom.core.models import CodeFile
from axiom.explanation.explanation_models import FileExplanation, FunctionExplanation


def _function_purpose(code_file: CodeFile, func_name: str) -> str:
    """Return docstring if present, otherwise infer a description from call graph."""
    symbol = next((s for s in code_file.symbols if s.name == func_name), None)
    if symbol and symbol.docstring:
        # Use the first sentence of the docstring
        first_line = symbol.docstring.strip().split("\n")[0].rstrip(".")
        return first_line
    return f"No docstring — inferred from call graph."


def _function_summary(func_name: str, calls: list[str], priority: float) -> str:
    parts: list[str] = []
    if calls:
        call_list = ", ".join(f"`{c}`" for c in sorted(calls)[:5])
        suffix = f" (and {len(calls) - 5} more)" if len(calls) > 5 else ""
        parts.append(f"Calls {call_list}{suffix}.")
    else:
        parts.append("No outbound calls detected.")
    if priority > 10:
        parts.append(f"Priority score: {priority:.1f} — review this function.")
    return " ".join(parts)


def _file_overview(code_file: CodeFile) -> str:
    n_funcs = sum(1 for s in code_file.symbols if s.symbol_type == "function")
    n_classes = sum(1 for s in code_file.symbols if s.symbol_type == "class")
    n_imports = len(code_file.imports)
    smell_names = [s.name for s in code_file.smells]

    parts = []
    if n_classes:
        parts.append(f"{n_classes} class{'es' if n_classes > 1 else ''}")
    if n_funcs:
        parts.append(f"{n_funcs} function{'s' if n_funcs > 1 else ''}")
    if n_imports:
        parts.append(f"{n_imports} import{'s' if n_imports > 1 else ''}")

    overview = f"Contains {', '.join(parts)}." if parts else "Empty or unparseable file."
    if smell_names:
        overview += f" Smells detected: {', '.join(smell_names)}."
    return overview


def explain_file(code_file: CodeFile) -> FileExplanation:
    functions = []
    for func_name, callees in code_file.call_graph.items():
        calls = sorted(callees)
        priority = code_file.priority.get(func_name, 0.0)
        functions.append(
            FunctionExplanation(
                name=func_name,
                purpose=_function_purpose(code_file, func_name),
                calls=calls,
                summary=_function_summary(func_name, calls, priority),
            )
        )

    # Sort by priority descending so most important functions appear first
    functions.sort(
        key=lambda f: code_file.priority.get(f.name, 0.0), reverse=True
    )

    return FileExplanation(
        path=code_file.path,
        overview=_file_overview(code_file),
        functions=functions,
        dependencies=code_file.imports,
        smells=[s.name for s in code_file.smells],
    )
