from __future__ import annotations
from typing import Any, Dict, List

class AutonomyScheduler:
    """126: continuously selects highest-value safe autonomous work."""

    def select(self, tasks: List[Dict[str, Any]], capacity: int = 5) -> List[Dict[str, Any]]:
        ready = []
        for task in tasks:
            if task.get("status", "queued") != "queued":
                continue
            if bool(task.get("blocked", False)):
                continue
            if bool(task.get("approval_required", False)) and not bool(task.get("approved", False)):
                continue

            value = float(task.get("value", 0))
            urgency = float(task.get("urgency", 0))
            learning = float(task.get("learning_value", 0))
            risk = float(task.get("risk", 0))
            score = value * 0.4 + urgency * 0.25 + learning * 0.25 - risk * 0.1
            ready.append({**task, "autonomy_score": round(score, 4)})

        ready.sort(key=lambda x: x["autonomy_score"], reverse=True)
        return ready[:max(1, int(capacity))]
