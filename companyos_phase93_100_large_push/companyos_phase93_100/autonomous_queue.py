from __future__ import annotations
from typing import Any, Dict, List

class AutonomousQueue:
    """94: priority queue for bounded autonomous internal work."""
    def select(self, tasks: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        ready = []
        for t in tasks:
            if t.get("status", "queued") != "queued":
                continue
            if bool(t.get("requires_external_action", False)):
                continue
            if bool(t.get("approval_required", False)) and not bool(t.get("approved", False)):
                continue
            score = float(t.get("priority", 0)) + float(t.get("value", 0)) - float(t.get("risk", 0))
            ready.append({**t, "queue_score": round(score, 4)})
        ready.sort(key=lambda x: x["queue_score"], reverse=True)
        return ready[:max(1, int(limit))]
