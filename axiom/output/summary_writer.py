from typing import Any, Dict

from axiom.core.models import ProjectIndex


def summarize_project(project: ProjectIndex) -> Dict[str, Any]:
    files = list(project.files.values())

    top_complex = sorted(files, key=lambda f: f.complexity, reverse=True)[:5]
    smelly_files = [f for f in files if f.smells]

    return {
        "total_files": len(files),
        "top_complex_files": [
            {"path": f.path, "complexity": f.complexity}
            for f in top_complex
        ],
        "files_with_smells": [
            {
                "path": f.path,
                "smells": [
                    {"name": s.name, "severity": s.severity, "message": s.message}
                    for s in f.smells
                ],
            }
            for f in smelly_files
        ],
    }
