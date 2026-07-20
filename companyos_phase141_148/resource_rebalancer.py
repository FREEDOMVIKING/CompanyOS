from __future__ import annotations
from typing import Any, Dict, List

class ResourceRebalancer:
    """147: autonomously shift internal compute/time budget toward stronger work."""

    def rebalance(self, ventures: List[Dict[str, Any]], total_capacity: float) -> Dict[str, Any]:
        total_capacity = max(0.0, float(total_capacity))
        scored = []
        for v in ventures:
            score = max(0.0, (
                float(v.get("traction", 0)) * .4
                + float(v.get("learning", 0)) * .25
                + float(v.get("margin", 0)) * .2
                + (1 - float(v.get("risk", 0))) * .15
            ))
            scored.append((score, v))
        denom = sum(s for s, _ in scored)
        allocations = []
        for score, venture in scored:
            amount = total_capacity * score / denom if denom else 0.0
            allocations.append({
                "venture": venture.get("name"),
                "capacity": round(amount, 4),
            })
        return {
            "total_capacity": total_capacity,
            "allocations": allocations,
            "autonomous_internal_rebalance": True,
        }
