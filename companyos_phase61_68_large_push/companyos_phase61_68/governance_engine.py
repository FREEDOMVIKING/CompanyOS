from __future__ import annotations
from typing import Any, Dict

class GovernanceEngine:
    """Phase 67: risk classification and approval policy."""
    def classify(self, action: Dict[str, Any]) -> Dict[str, Any]:
        external = bool(action.get("external", False))
        financial = bool(action.get("financial", False))
        irreversible = bool(action.get("irreversible", False))
        user_impact = max(0, int(action.get("user_impact", 0)))

        risk = 0
        risk += 2 if external else 0
        risk += 3 if financial else 0
        risk += 4 if irreversible else 0
        risk += min(3, user_impact)

        level = "low" if risk <= 2 else "medium" if risk <= 5 else "high"
        approval_required = risk >= 6
        return {
            "risk_score": risk,
            "risk_level": level,
            "approval_required": approval_required,
            "allowed": (not approval_required) or bool(action.get("explicit_approval", False)),
        }
