"""Tests for call graph and analysis."""
from axiom.analysis.call_graph import build_call_graph
from tests.conftest import SIMPLE_SOURCE, DOCSTRING_SOURCE


class TestBuildCallGraph:
    def test_direct_calls_tracked(self):
        graph = build_call_graph(SIMPLE_SOURCE)
        assert "compute" in graph
        assert "add" in graph["compute"]
        assert "subtract" in graph["compute"]

    def test_no_outbound_calls(self):
        graph = build_call_graph(SIMPLE_SOURCE)
        # add and subtract don't call anything
        assert "add" not in graph or len(graph["add"]) == 0
        assert "subtract" not in graph or len(graph["subtract"]) == 0

    def test_attribute_call_tracked(self):
        graph = build_call_graph(DOCSTRING_SOURCE)
        # method calls self.greet — 'greet' should be in its callees
        assert "method" in graph
        assert "greet" in graph["method"]

    def test_invalid_source_returns_empty(self):
        assert build_call_graph("def (bad") == {}

    def test_async_function_tracked(self):
        src = "async def runner():\n    await helper()\n"
        graph = build_call_graph(src)
        assert "runner" in graph
        assert "helper" in graph["runner"]
