import json
import sys
from pathlib import Path

from axiom.orchestration.pipeline import run_analysis, run_explanation
from axiom.output.json_writer import write_json
from axiom.output.markdown_writer import write_markdown
from axiom.output.summary_writer import summarize_project


def analyze_command(args) -> None:
    path = Path(args.path)
    if not path.exists():
        print(f"Error: path does not exist: {path}", file=sys.stderr)
        sys.exit(1)
    if not path.is_dir():
        print(f"Error: path is not a directory: {path}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {path.resolve()} ...")
    project = run_analysis(args.path)
    n = len(project.files)
    print(f"Found {n} Python file{'s' if n != 1 else ''}.\n")

    if n == 0:
        print("No Python files found. Nothing to analyze.")
        return

    # Always generate explanations
    explanations = run_explanation(project)

    # --output: write markdown report
    if args.output:
        write_markdown(explanations, args.output)
        print(f"Markdown report written to: {args.output}")

    # --summary: print or write summary (does NOT suppress the markdown report)
    if args.summary:
        summary = summarize_project(project)
        if args.json:
            write_json(summary, args.json)
            print(f"JSON summary written to: {args.json}")
        else:
            print(json.dumps(summary, indent=2, default=str))
        return

    # Default: print a brief result to stdout when no file output was requested
    if not args.output:
        smelly = sum(1 for f in project.files.values() if f.smells)
        top = sorted(project.files.values(), key=lambda f: f.complexity, reverse=True)[:3]
        print("Top files by complexity:")
        for f in top:
            print(f"  {Path(f.path).name:40s}  complexity={f.complexity}")
        if smelly:
            print(f"\n{smelly} file(s) have code smells. Run with --output report.md for details.")
        else:
            print("\nNo code smells detected.")
        print("\nRun with --output <file.md> to write a full report.")
