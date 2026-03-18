import sys
from pathlib import Path

from axiom.orchestration.pipeline import run_analysis, run_explanation


def explain_command(args) -> None:
    path = Path(args.path)
    if not path.exists():
        print(f"Error: path does not exist: {path}", file=sys.stderr)
        sys.exit(1)
    if not path.is_dir():
        print(f"Error: path is not a directory: {path}", file=sys.stderr)
        sys.exit(1)

    project = run_analysis(args.path)
    explanations = run_explanation(project)

    if not explanations:
        print("No Python files found.")
        return

    for file_path, explanation in explanations.items():
        display = Path(file_path).name
        print(f"\n{'=' * 60}")
        print(f"  {display}")
        print(f"{'=' * 60}")
        print(explanation.overview)

        if explanation.smells:
            print(f"  Smells: {', '.join(explanation.smells)}")

        if explanation.functions:
            print()
            for fn in explanation.functions:
                print(f"  [{fn.name}]")
                print(f"    {fn.purpose}")
                print(f"    {fn.summary}")
