from axiom.parsing.project_indexer import index_project
from axiom.analysis.project_analyzer import analyze_project
from axiom.explanation.explanation_engine import explain_file


def run_analysis(path):
    project = index_project(path)
    analyze_project(project)
    return project


def run_explanation(project):
    explanations = {}
    for file in project.files.values():
        explanations[file.path] = explain_file(file)
    return explanations
