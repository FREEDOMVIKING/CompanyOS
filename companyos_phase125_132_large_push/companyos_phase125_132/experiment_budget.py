from __future__ import annotations
from typing import Any, Dict

class ExperimentBudget:
    """129: allow autonomous experiments inside explicit spend/risk ceilings."""

    def authorize(
        self,
        requested_cost: float,
        remaining_budget: float,
        risk_score: float,
        max_risk: float = 0.35,
    ) -> Dict[str, Any]:
        requested_cost = max(0.0, float(requested_cost))
        remaining_budget = max(0.0, float(remaining_budget))
        risk_score = max(0.0, min(1.0, float(risk_score)))
        max_risk = max(0.0, min(1.0, float(max_risk)))

        allowed = requested_cost <= remaining_budget and risk_score <= max_risk
        return {
            "allowed": allowed,
            "approval_required": not allowed,
            "requested_cost": requested_cost,
            "remaining_budget": remaining_budget,
            "risk_score": risk_score,
            "max_risk": max_risk,
        }
