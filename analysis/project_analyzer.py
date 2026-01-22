from axiom.analysis.file_analyzer import analyze_file


def analyze_project(project_index):
    for file in project_index.files.values():
        analyze_file(file)
    return project_index
