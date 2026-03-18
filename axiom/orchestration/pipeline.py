from pathlib import Path
from typing import Dict

from axiom.analysis.project_analyzer import analyze_project
from axiom.core.models import ProjectIndex
from axiom.core.project_scanner import scan_project
from axiom.explanation.explanation_engine import explain_file
from axiom.explanation.explanation_models import FileExplanation
from axiom.output.html_writer import write_html


def run_analysis(path: str) -> ProjectIndex:
    project = scan_project(Path(path))
    analyze_project(project)
    return project


def run_explanation(project: ProjectIndex) -> Dict[str, FileExplanation]:
    return {
        file_path: explain_file(code_file)
        for file_path, code_file in project.files.items()
    }


def run_html_report(project: ProjectIndex, output_path: str) -> None:
    write_html(project, output_path)
