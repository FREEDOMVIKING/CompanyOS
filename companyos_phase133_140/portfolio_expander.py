from __future__ import annotations
from typing import Any, Dict, List

class PortfolioExpander:
    """139: identify when to add, clone, iterate, or retire ventures."""

    def decide(self, ventures: List[Dict[str, Any]], max_active: int = 5) -> Dict[str, Any]:
        active = [v for v in ventures if v.get("status", "active") == "active"]
        strong = [
            v for v in active
            if float(v.get("traction", 0)) >= 0.7 and float(v.get("margin", 0)) >= 0.5
        ]
        weak = [
            v for v in active
            if float(v.get("traction", 0)) < 0.25 and float(v.get("learning", 0)) < 0.35
        ]
        can_expand = len(active) < max(1, int(max_active)) and bool(strong)
        return {
            "active_count": len(active),
            "strong_ventures": [v.get("name") for v in strong],
            "weak_ventures": [v.get("name") for v in weak],
            "autonomous_expansion_allowed": can_expand,
            "recommendation": "launch_new_internal_validation" if can_expand else "optimize_existing_portfolio",
        }
