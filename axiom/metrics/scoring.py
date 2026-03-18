def priority_score(complexity: int, importance: float) -> float:
    """
    Weighted priority score: 60% complexity, 40% importance.
    Higher score = more important to review first.
    """
    return round((0.6 * complexity) + (0.4 * importance), 2)
