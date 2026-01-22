from axiom.explanation.explanation_models import (
    FileExplanation,
    FunctionExplanation,
)


def explain_file(code_file):
    functions = []

    for func, calls in code_file.call_graph.items():
        functions.append(
            FunctionExplanation(
                name=func,
                purpose="Function extracted from source code.",
                calls=list(calls),
                summary=f"{func} calls {len(calls)} other functions.",
            )
        )

    return FileExplanation(
        path=code_file.path,
        overview="Automatically generated explanation of file structure.",
        functions=functions,
        dependencies=code_file.imports,
    )
