from __future__ import annotations
from typing import Any, Dict, List, Set

class TaskGraph:
    """Phase 62: dependency-aware task ordering and deadlock detection."""
    def order(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        by_id = {str(t["id"]): dict(t) for t in tasks}
        done: Set[str] = set()
        ordered: List[Dict[str, Any]] = []
        remaining = set(by_id)

        while remaining:
            progressed = False
            for tid in list(remaining):
                deps = {str(x) for x in by_id[tid].get("depends_on", [])}
                if deps.issubset(done):
                    ordered.append(by_id[tid])
                    done.add(tid)
                    remaining.remove(tid)
                    progressed = True
            if not progressed:
                return {
                    "success": False,
                    "status": "dependency_deadlock",
                    "blocked": sorted(remaining),
                    "ordered": ordered,
                }

        return {"success": True, "status": "ordered", "ordered": ordered}
