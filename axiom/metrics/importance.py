from typing import Dict, Set


def compute_importance(call_graph: Dict[str, Set[str]]) -> Dict[str, float]:
    """
    Compute a simple importance score for each function using degree centrality.

    Score = (number of functions that call this function) * 2
            + (number of functions this function calls)

    Callee weight is higher because being called by many others is a stronger
    signal of importance than calling many others.
    """
    all_functions: set[str] = set(call_graph.keys())
    # also include functions that appear as callees but have no outbound calls
    for callees in call_graph.values():
        all_functions.update(callees)

    scores: Dict[str, float] = {}
    for fn in all_functions:
        inbound = sum(fn in callees for callees in call_graph.values())
        outbound = len(call_graph.get(fn, set()))
        scores[fn] = float(inbound * 2 + outbound)

    return scores
