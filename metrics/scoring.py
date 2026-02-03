def priority_score(complexity: int, importance: int) -> float:
    return round((0.6 * complexity) + (0.4 * importance), 2)
