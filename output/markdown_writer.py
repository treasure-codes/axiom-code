def write_markdown(explanations, output_path):
    lines = []

    for path, explanation in explanations.items():
        lines.append(f"# {path}\n")
        lines.append(explanation.overview + "\n")

        for fn in explanation.functions:
            lines.append(f"## Function: {fn.name}")
            lines.append(f"- Calls: {', '.join(fn.calls) or 'None'}")
            lines.append(f"- Summary: {fn.summary}\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
