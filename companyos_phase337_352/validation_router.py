from __future__ import annotations

class ValidationRouter:
    """347: decide what validation action a ranked opportunity needs next."""

    def route(self, ranked):
        routed = []
        for item in ranked:
            score = float(item.get("score", 0))
            if not item.get("valid"):
                action = "reject_invalid"
            elif score >= 7.5:
                action = "priority_validation"
            elif score >= 5.5:
                action = "light_validation"
            else:
                action = "archive_or_research_more"
            routed.append({**item, "next_action": action})
        return routed
