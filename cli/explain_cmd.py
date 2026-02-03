from axiom.orchestration.pipeline import run_analysis, run_explanation


def explain_command(args):
    project = run_analysis(args.path)
    explanations = run_explanation(project)

    for path, explanation in explanations.items():
        print(f"\n{path}")
        print(explanation.overview)
        for fn in explanation.functions:
            print(f"- {fn.name}: {fn.summary}")
