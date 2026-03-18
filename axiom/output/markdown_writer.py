from pathlib import Path
from typing import Dict

from axiom.explanation.explanation_models import FileExplanation


def write_markdown(explanations: Dict[str, FileExplanation], output_path: str) -> None:
    lines = []

    for path, explanation in explanations.items():
        # Use just the filename for the header to keep it readable
        display_name = Path(path).name
        lines.append(f"# {display_name}")
        lines.append(f"**Path:** `{path}`\n")
        lines.append(explanation.overview)

        if explanation.smells:
            lines.append("\n**Code Smells:**")
            for smell in explanation.smells:
                lines.append(f"- {smell}")

        if explanation.dependencies:
            lines.append("\n**Imports:** " + ", ".join(f"`{d}`" for d in explanation.dependencies))

        if explanation.functions:
            lines.append("\n## Functions\n")
            for fn in explanation.functions:
                lines.append(f"### `{fn.name}`")
                lines.append(f"**Purpose:** {fn.purpose}")
                if fn.calls:
                    lines.append(f"**Calls:** {', '.join(f'`{c}`' for c in fn.calls)}")
                lines.append(f"**Summary:** {fn.summary}\n")

        lines.append("\n---\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
