import logging
from pathlib import Path
from typing import Dict, List, Set

from axiom.core.models import ProjectIndex

logger = logging.getLogger(__name__)


def build_file_dependency_graph(project: ProjectIndex) -> Dict[str, List[str]]:
    """
    Build a map of file_path -> [file_paths it directly imports from],
    restricted to files that exist within the project.
    """
    # Build lookup: every possible dotted suffix of a file's path -> full path
    # e.g. "axiom/core/models.py" registers "models", "core.models", "axiom.core.models"
    suffix_to_path: Dict[str, str] = {}
    for path in project.files:
        parts = list(Path(path).with_suffix("").parts)
        for i in range(len(parts)):
            key = ".".join(parts[i:])
            suffix_to_path[key] = path

    dependencies: Dict[str, List[str]] = {}
    for path, code_file in project.files.items():
        deps: Set[str] = set()
        for imp in code_file.imports:
            target = suffix_to_path.get(imp)
            if target and target != path:
                deps.add(target)
        dependencies[path] = sorted(deps)

    return dependencies


def find_dead_code(project: ProjectIndex) -> Dict[str, List[str]]:
    """
    Find functions that are defined but never called anywhere in the project.
    Returns: {file_path: [dead_function_names]}
    Public functions only (skips names starting with _).
    """
    all_called: Set[str] = set()
    for code_file in project.files.values():
        for callees in code_file.call_graph.values():
            all_called.update(callees)

    dead: Dict[str, List[str]] = {}
    for path, code_file in project.files.items():
        dead_fns = [
            s.name
            for s in code_file.symbols
            if s.symbol_type == "function"
            and s.name not in all_called
            and not s.name.startswith("_")
        ]
        if dead_fns:
            dead[path] = dead_fns

    return dead


def find_circular_imports(dependencies: Dict[str, List[str]]) -> List[List[str]]:
    """
    Detect import cycles using DFS.
    Returns a list of cycles, each cycle is a list of file paths forming the loop.
    """
    cycles: List[List[str]] = []
    visited: Set[str] = set()
    rec_stack: Set[str] = set()
    path_stack: List[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        rec_stack.add(node)
        path_stack.append(node)

        for neighbor in dependencies.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                idx = path_stack.index(neighbor)
                cycle = path_stack[idx:] + [neighbor]
                if cycle not in cycles:
                    cycles.append(cycle)

        path_stack.pop()
        rec_stack.discard(node)

    for node in list(dependencies.keys()):
        if node not in visited:
            dfs(node)

    return cycles
