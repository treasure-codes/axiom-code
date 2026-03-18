import argparse
import sys

from axiom import __version__
from axiom.cli.analyze_cmd import analyze_command
from axiom.cli.explain_cmd import explain_command
from axiom.config import initialize_dirs
from axiom.utils.logger import setup_logging


def main() -> None:
    setup_logging()
    initialize_dirs()

    parser = argparse.ArgumentParser(
        prog="axiom",
        description="Axiom-Code: Autonomous Semantic Analysis & Interpretability Engine",
    )
    parser.add_argument("--version", action="version", version=f"axiom {__version__}")

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # --- analyze ---
    analyze = sub.add_parser("analyze", help="Analyze a project directory")
    analyze.add_argument("path", help="Path to the project root")
    analyze.add_argument("--html", metavar="FILE", help="Write visual HTML report to FILE")
    analyze.add_argument("--output", metavar="FILE", help="Write Markdown report to FILE")
    analyze.add_argument("--summary", action="store_true", help="Print a ranked project summary")
    analyze.add_argument("--json", metavar="FILE", help="Write JSON summary to FILE (requires --summary)")
    analyze.set_defaults(func=analyze_command)

    # --- explain ---
    explain = sub.add_parser("explain", help="Print per-file explanations to stdout")
    explain.add_argument("path", help="Path to the project root")
    explain.set_defaults(func=explain_command)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
