from axiom.orchestration.pipeline import run_analysis, run_explanation
from axiom.output.markdown_writer import write_markdown


def analyze_command(args):
    project = run_analysis(args.path)
    explanations = run_explanation(project)

    if args.output:
        write_markdown(explanations, args.output)
    else:
        print("Analysis complete.")
