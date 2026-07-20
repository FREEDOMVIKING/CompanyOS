from __future__ import annotations
from typing import Any, Dict

class ExternalActionRouter:
    """98: route external actions through approval and connector boundaries."""
    ALWAYS_APPROVAL = {"send_payment", "purchase", "sign_contract", "deploy_production", "publish_public"}

    def route(self, action: Dict[str, Any]) -> Dict[str, Any]:
        action_type = str(action.get("type", "unknown"))
        external = bool(action.get("external", True))
        irreversible = bool(action.get("irreversible", False))
        approval_required = action_type in self.ALWAYS_APPROVAL or irreversible
        approved = bool(action.get("approved", False))
        return {
            "action_type": action_type,
            "external": external,
            "approval_required": approval_required,
            "approved": approved,
            "dispatch_allowed": (not approval_required) or approved,
            "dispatched": False,
        }
