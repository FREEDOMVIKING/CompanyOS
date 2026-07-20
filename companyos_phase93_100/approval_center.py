from __future__ import annotations
from typing import Any, Dict, List

class ApprovalCenter:
    """96: centralized approval queue and decision records."""
    def pending(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [a for a in actions if bool(a.get("approval_required", False)) and not bool(a.get("approved", False))]

    def decide(self, action: Dict[str, Any], approved: bool, reason: str = "") -> Dict[str, Any]:
        return {
            **action,
            "approved": bool(approved),
            "approval_decision_recorded": True,
            "approval_reason": reason,
        }
