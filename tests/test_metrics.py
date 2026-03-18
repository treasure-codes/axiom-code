"""Tests for metrics: complexity, importance, scoring."""
from axiom.metrics.complexity import compute_complexity
from axiom.metrics.importance import compute_importance
from axiom.metrics.scoring import priority_score


class TestComplexity:
    def test_empty_file(self):
        assert compute_complexity("") == 1

    def test_single_function_no_branches(self):
        src = "def foo():\n    return 1\n"
        assert compute_complexity(src) == 1

    def test_if_adds_complexity(self):
        src = "if x:\n    pass\n"
        assert compute_complexity(src) >= 2

    def test_for_adds_complexity(self):
        src = "for i in range(10):\n    pass\n"
        assert compute_complexity(src) >= 2

    def test_while_adds_complexity(self):
        src = "while True:\n    break\n"
        assert compute_complexity(src) >= 2

    def test_try_except_adds_per_handler(self):
        src = (
            "try:\n    pass\n"
            "except ValueError:\n    pass\n"
            "except TypeError:\n    pass\n"
        )
        score = compute_complexity(src)
        assert score >= 3  # base 1 + 2 handlers

    def test_invalid_source_returns_zero(self):
        assert compute_complexity("def (bad") == 0

    def test_bool_op_adds_complexity(self):
        src = "x = a and b and c\n"
        score = compute_complexity(src)
        assert score >= 3  # base 1 + 2 (three values → 2 extra branches)


class TestImportance:
    def test_empty_graph(self):
        assert compute_importance({}) == {}

    def test_called_function_scores_higher(self):
        graph = {"main": {"helper"}, "helper": set()}
        scores = compute_importance(graph)
        # helper is called by main → higher inbound score
        assert scores["helper"] >= scores.get("main", 0)

    def test_all_functions_scored(self):
        graph = {"a": {"b", "c"}, "b": {"c"}}
        scores = compute_importance(graph)
        assert "a" in scores
        assert "b" in scores
        assert "c" in scores


class TestPriorityScore:
    def test_zero_inputs(self):
        assert priority_score(0, 0) == 0.0

    def test_complexity_weighted_more(self):
        # complexity weight is 0.6, importance is 0.4
        s1 = priority_score(10, 0)
        s2 = priority_score(0, 10)
        assert s1 > s2

    def test_returns_float(self):
        result = priority_score(5, 3)
        assert isinstance(result, float)
