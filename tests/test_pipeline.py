"""Integration test: full pipeline on a temporary project directory."""
import json
import os
import tempfile
from pathlib import Path

import pytest

from axiom.orchestration.pipeline import run_analysis, run_explanation
from axiom.output.markdown_writer import write_markdown
from axiom.output.json_writer import write_json
from axiom.output.summary_writer import summarize_project


FIXTURE_SOURCE = """\
import os

def read_data(path):
    \"\"\"Read lines from a file.\"\"\"
    with open(path) as f:
        return f.readlines()

def process(lines):
    result = []
    for line in lines:
        if line.strip():
            result.append(line.upper())
    return result

def main():
    data = read_data("input.txt")
    output = process(data)
    for line in output:
        print(line)
"""


@pytest.fixture
def project_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "main.py").write_text(FIXTURE_SOURCE, encoding="utf-8")
        (Path(tmpdir) / "empty.py").write_text("", encoding="utf-8")
        yield tmpdir


class TestPipeline:
    def test_scan_finds_python_files(self, project_dir):
        project = run_analysis(project_dir)
        assert len(project.files) >= 1
        assert any("main.py" in p for p in project.files)

    def test_analysis_populates_complexity(self, project_dir):
        project = run_analysis(project_dir)
        main_file = next(f for p, f in project.files.items() if "main.py" in p)
        assert main_file.complexity > 0

    def test_analysis_populates_symbols(self, project_dir):
        project = run_analysis(project_dir)
        main_file = next(f for p, f in project.files.items() if "main.py" in p)
        names = [s.name for s in main_file.symbols]
        assert "read_data" in names
        assert "process" in names
        assert "main" in names

    def test_analysis_populates_call_graph(self, project_dir):
        project = run_analysis(project_dir)
        main_file = next(f for p, f in project.files.items() if "main.py" in p)
        assert "main" in main_file.call_graph
        assert "read_data" in main_file.call_graph["main"]
        assert "process" in main_file.call_graph["main"]

    def test_explanation_uses_docstring(self, project_dir):
        project = run_analysis(project_dir)
        explanations = run_explanation(project)
        main_path = next(p for p in explanations if "main.py" in p)
        read_data_fn = next(
            (fn for fn in explanations[main_path].functions if fn.name == "read_data"),
            None,
        )
        assert read_data_fn is not None
        assert "Read lines" in read_data_fn.purpose

    def test_markdown_output_written(self, project_dir):
        project = run_analysis(project_dir)
        explanations = run_explanation(project)
        out = os.path.join(project_dir, "report.md")
        write_markdown(explanations, out)
        assert Path(out).exists()
        content = Path(out).read_text(encoding="utf-8")
        assert "main.py" in content

    def test_json_summary_serializable(self, project_dir):
        project = run_analysis(project_dir)
        summary = summarize_project(project)
        out = os.path.join(project_dir, "summary.json")
        write_json(summary, out)
        loaded = json.loads(Path(out).read_text(encoding="utf-8"))
        assert "total_files" in loaded
        assert "top_complex_files" in loaded

    def test_scanner_skips_non_python(self, project_dir):
        (Path(project_dir) / "notes.txt").write_text("hello", encoding="utf-8")
        project = run_analysis(project_dir)
        assert not any("notes.txt" in p for p in project.files)

    def test_invalid_path_raises(self):
        with pytest.raises(ValueError):
            run_analysis("/nonexistent/path/xyz")
