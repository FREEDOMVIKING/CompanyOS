from __future__ import annotations
from typing import Any, Dict, List

class CustomerAcquisitionEngine:
    """143: rank acquisition channels and create autonomous test plans."""

    def rank_channels(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for c in channels:
            reach = float(c.get("reach", 0))
            intent = float(c.get("intent", 0))
            cost_efficiency = float(c.get("cost_efficiency", 0))
            speed = float(c.get("speed", 0))
            score = reach * .25 + intent * .35 + cost_efficiency * .25 + speed * .15
            out.append({
                **c,
                "acquisition_score": round(score, 4),
                "test_autonomously": bool(c.get("reversible", True) and c.get("bounded", True)),
            })
        return sorted(out, key=lambda x: x["acquisition_score"], reverse=True)
