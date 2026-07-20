from __future__ import annotations
from typing import Any, Dict, List

class ContinuousExecutor:
    """136: keep internal autonomous work moving without manual prompting."""

    def next_batch(self, tasks: List[Dict[str, Any]], capacity: int = 5) -> List[Dict[str, Any]]:
        ready = []
        for t in tasks:
            if t.get("status", "queued") != "queued":
                continue
            if bool(t.get("blocked", False)):
                continue
            if bool(t.get("approval_required", False)) and not bool(t.get("approved", False)):
                continue
            score = (
                float(t.get("priority", 0)) * 0.35
                + float(t.get("value", 0)) * 0.35
                + float(t.get("learning_value", 0)) * 0.20
                - float(t.get("risk", 0)) * 0.10
            )
            ready.append({**t, "execution_score": round(score, 4)})
        ready.sort(key=lambda x: x["execution_score"], reverse=True)
        return ready[:max(1, int(capacity))]
