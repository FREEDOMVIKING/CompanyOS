from __future__ import annotations
from typing import Any, Dict, List

class ResourcePlanner:
    """Phase 63: allocate time/capacity to highest-value internal work."""
    def allocate(self, tasks: List[Dict[str, Any]], capacity: float) -> Dict[str, Any]:
        capacity = max(0.0, float(capacity))
        ranked = sorted(
            tasks,
            key=lambda t: float(t.get("value", 0)) / max(1.0, float(t.get("cost", 1))),
            reverse=True,
        )
        chosen, deferred = [], []
        used = 0.0
        for task in ranked:
            cost = max(0.0, float(task.get("cost", 0)))
            if used + cost <= capacity:
                chosen.append(task)
                used += cost
            else:
                deferred.append(task)
        return {
            "capacity": capacity,
            "used": round(used, 4),
            "remaining": round(capacity - used, 4),
            "chosen": chosen,
            "deferred": deferred,
        }
