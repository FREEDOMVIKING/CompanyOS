from __future__ import annotations
from typing import Any, Dict

class ApprovalGuard:
    """Phase 56: explicit guardrail for irreversible or externally consequential actions."""
    HIGH_IMPACT = {
        "send_payment", "transfer_funds", "publish_external", "sign_contract",
        "delete_external", "purchase", "deploy_production", "send_email_external",
    }

    def evaluate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        action_type = str(action.get("type", "")).lower()
        irreversible = bool(action.get("irreversible", False))
        high_impact = action_type in self.HIGH_IMPACT or irreversible
        approved = bool(action.get("explicit_approval", False))
        return {
            "allowed": (not high_impact) or approved,
            "approval_required": high_impact,
            "explicit_approval": approved,
            "action_type": action_type,
        }
