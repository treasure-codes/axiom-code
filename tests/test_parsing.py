"""Tests for the parsing layer."""
from axiom.parsing.ast_parser import PythonASTParser, safe_parse
from axiom.parsing.dependency_graph import extract_imports
from axiom.parsing.symbol_table import extract_symbols
from tests.conftest import SIMPLE_SOURCE, DOCSTRING_SOURCE


class TestSafeParse:
    def test_valid_source(self):
        tree = safe_parse("x = 1")
        assert tree is not None

    def test_syntax_error_returns_none(self):
        assert safe_parse("def (bad syntax") is None

    def test_empty_source(self):
        tree = safe_parse("")
        assert tree is not None


class TestExtractSymbols:
    def test_finds_functions(self):
        symbols = extract_symbols(SIMPLE_SOURCE)
        names = [s.name for s in symbols]
        assert "add" in names
        assert "subtract" in names
        assert "compute" in names

    def test_symbol_types(self):
        symbols = extract_symbols(SIMPLE_SOURCE)
        for s in symbols:
            assert s.symbol_type == "function"

    def test_finds_class(self):
        symbols = extract_symbols(DOCSTRING_SOURCE)
        class_symbols = [s for s in symbols if s.symbol_type == "class"]
        assert len(class_symbols) == 1
        assert class_symbols[0].name == "MyClass"

    def test_extracts_docstring(self):
        symbols = extract_symbols(DOCSTRING_SOURCE)
        greet = next(s for s in symbols if s.name == "greet")
        assert greet.docstring == "Return a greeting for the given name."

    def test_async_function_extracted(self):
        symbols = extract_symbols(DOCSTRING_SOURCE)
        names = [s.name for s in symbols]
        assert "fetch" in names

    def test_invalid_source_returns_empty(self):
        assert extract_symbols("def (bad") == []

    def test_line_numbers(self):
        symbols = extract_symbols(SIMPLE_SOURCE)
        add_sym = next(s for s in symbols if s.name == "add")
        assert add_sym.lineno == 1


class TestExtractImports:
    def test_regular_import(self):
        imports = extract_imports("import os\nimport sys")
        assert "os" in imports
        assert "sys" in imports

    def test_from_import(self):
        imports = extract_imports("from pathlib import Path")
        assert "pathlib" in imports

    def test_no_imports(self):
        assert extract_imports("x = 1") == []

    def test_invalid_source_returns_empty(self):
        assert extract_imports("def (bad") == []

    def test_sorted_output(self):
        imports = extract_imports("import sys\nimport os\nimport ast")
        assert imports == sorted(imports)
