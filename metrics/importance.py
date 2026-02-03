def compute_importance(call_graph: dict) -> dict:
    scores = {}

    for fn in call_graph:
        inbound = sum(fn in calls for calls in call_graph.values())
        outbound = len(call_graph.get(fn, []))
        scores[fn] = inbound + outbound

    return scores
