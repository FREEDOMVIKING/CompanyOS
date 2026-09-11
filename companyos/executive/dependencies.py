from typing import Dict, List, Set
from .models import Venture


def analyze_dependencies(ventures: List[Venture]) -> Dict:
    ids = {v.venture_id for v in ventures}
    missing = {}
    graph = {}
    for v in ventures:
        graph[v.venture_id] = [d for d in v.dependencies if d in ids]
        unknown = [d for d in v.dependencies if d not in ids]
        if unknown:
            missing[v.venture_id] = unknown

    cycles = _find_cycles(graph)
    blocked_by_dependency = sorted({
        node for cycle in cycles for node in cycle
    } | set(missing.keys()))

    return {
        "graph": graph,
        "missing_dependencies": missing,
        "cycles": cycles,
        "blocked_by_dependency": blocked_by_dependency,
    }


def _find_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    cycles: List[List[str]] = []
    visiting: Set[str] = set()
    visited: Set[str] = set()
    path: List[str] = []

    def walk(node: str) -> None:
        if node in visiting:
            start = path.index(node)
            cycle = path[start:] + [node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        visiting.add(node)
        path.append(node)
        for nxt in graph.get(node, []):
            walk(nxt)
        path.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        walk(node)
    return cycles
