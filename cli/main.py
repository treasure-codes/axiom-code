import argparse
from axiom.cli.analyze_cmd import analyze_command
from axiom.cli.explain_cmd import explain_command


def main():
    parser = argparse.ArgumentParser(prog="axiom")
    sub = parser.add_subparsers(dest="command")

    analyze = sub.add_parser("analyze")
    analyze.add_argument("path")
    analyze.add_argument("--output", help="Write Markdown report")
    analyze.add_argument("--summary", action="store_true", help="Show ranked project summary")
    analyze.add_argument("--json", help="Write JSON output")
    analyze.set_defaults(func=analyze_command)

    explain = sub.add_parser("explain")
    explain.add_argument("path")
    explain.set_defaults(func=explain_command)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
