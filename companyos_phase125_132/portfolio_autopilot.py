from __future__ import annotations
from typing import Any, Dict, List

class PortfolioAutopilot:
    """131: autonomously continue, iterate, pause, or retire internal ventures."""

    def review(self, ventures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for v in ventures:
            traction = float(v.get("traction", 0))
            margin = float(v.get("margin", 0))
            learning = float(v.get("learning", 0))
            risk = float(v.get("risk", 0))
            score = traction * 0.4 + margin * 0.25 + learning * 0.2 + (1-risk) * 0.15

            if score >= 0.72:
                action = "continue_and_scale_internal_capacity"
            elif score >= 0.48:
                action = "iterate_and_retest"
            elif score >= 0.30:
                action = "pause_and_revalidate"
            else:
                action = "retire_internal_project"

            out.append({**v, "portfolio_score": round(score, 4), "autonomous_action": action})
        return sorted(out, key=lambda x: x["portfolio_score"], reverse=True)
