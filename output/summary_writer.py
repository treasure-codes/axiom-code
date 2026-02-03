def summarize_project(project):
    files = list(project.files.values())

    top_complex = sorted(
        files,
        key=lambda f: getattr(f, "complexity", 0),
        reverse=True
    )[:5]

    top_smelly = [f for f in files if getattr(f, "smells", [])]

    return {
        "top_complex_files": [
            {"path": f.path, "complexity": f.complexity}
            for f in top_complex
        ],
        "files_with_smells": [
            {"path": f.path, "smells": f.smells}
            for f in top_smelly
        ]
    }
