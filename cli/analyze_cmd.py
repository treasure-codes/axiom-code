from axiom.orchestration.pipeline import run_analysis, run_explanation
from axiom.output.markdown_writer import write_markdown
from axiom.output.json_writer import write_json
from axiom.output.summary_writer import summarize_project


def analyze_command(args):
    project = run_analysis(args.path)

    if args.summary:
        summary = summarize_project(project)
        if args.json:
            write_json(summary, args.json)
        else:
            print(summary)
        return

    explanations = run_explanation(project)

    if args.output:
        write_markdown(explanations, args.output)
    else:
        print("Analysis complete.")
