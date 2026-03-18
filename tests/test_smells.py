"""Tests for smell detectors."""
import pytest
from axiom.core.models import CodeFile
from axiom.smells.complexity_smells import HighComplexitySmell
from axiom.smells.structural_smells import GodFileSmell
from axiom.analysis.file_analyzer import analyze_file
from tests.conftest import SIMPLE_SOURCE, COMPLEX_SOURCE


class TestHighComplexitySmell:
    def _analyzed(self, source: str) -> CodeFile:
        f = CodeFile(path="test.py", language="python", source=source)
        return analyze_file(f)

    def test_no_smell_on_simple_code(self):
        f = self._analyzed(SIMPLE_SOURCE)
        smell = HighComplexitySmell().detect(f)
        assert smell is None

    def test_smell_detected_on_complex_code(self):
        f = self._analyzed(COMPLEX_SOURCE)
        smell = HighComplexitySmell().detect(f)
        assert smell is not None
        assert smell.name == "High Complexity"

    def test_smell_has_severity(self):
        f = self._analyzed(COMPLEX_SOURCE)
        smell = HighComplexitySmell().detect(f)
        assert smell.severity in ("low", "medium", "high")

    def test_smell_metadata_has_score(self):
        f = self._analyzed(COMPLEX_SOURCE)
        smell = HighComplexitySmell().detect(f)
        assert "score" in smell.metadata
        assert smell.metadata["score"] > 15


class TestGodFileSmell:
    def _file_with_n_symbols(self, n: int) -> CodeFile:
        source = "\n".join(f"def func_{i}(): pass" for i in range(n))
        f = CodeFile(path="test.py", language="python", source=source)
        return analyze_file(f)

    def test_no_smell_below_threshold(self):
        f = self._file_with_n_symbols(5)
        assert GodFileSmell().detect(f) is None

    def test_smell_above_threshold(self):
        f = self._file_with_n_symbols(15)
        smell = GodFileSmell().detect(f)
        assert smell is not None
        assert smell.name == "God File"

    def test_severity_field_present(self):
        f = self._file_with_n_symbols(15)
        smell = GodFileSmell().detect(f)
        assert smell.severity in ("low", "medium", "high")
