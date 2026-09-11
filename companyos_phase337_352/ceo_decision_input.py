from __future__ import annotations

class CEODecisionInput:
    """348: concise CEO decision packet from research results."""

    def build(self, routed, network_health):
        return {
            "recommended_candidates": [
                {
                    "name": x.get("opportunity", {}).get("name"),
                    "score": x.get("score"),
                    "next_action": x.get("next_action"),
                    "validation_plan": x.get("validation_plan"),
                }
                for x in routed[:5]
            ],
            "network_health": network_health,
            "decision_rule": "validate evidence before major build commitment",
        }
