from __future__ import annotations
from typing import Any, Dict

class AuthorityModel:
    """125: autonomy-first authority model.

    Internal, reversible, bounded actions are allowed automatically.
    Approval is reserved for irreversible, legal, destructive, or
    budget-exceeding actions.
    """

    ALWAYS_REVIEW = {
        "sign_contract",
        "legal_commitment",
        "delete_external_resource",
        "transfer_funds",
        "purchase_over_limit",
        "publish_regulated_claim",
    }

    def evaluate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        action_type = str(action.get("type", "internal"))
        irreversible = bool(action.get("irreversible", False))
        destructive = bool(action.get("destructive", False))
        legal = bool(action.get("legal_commitment", False))
        requested = max(0.0, float(action.get("requested_budget", 0.0)))
        autonomous_limit = max(0.0, float(action.get("autonomous_budget_limit", 0.0)))
        exceeds_budget = requested > autonomous_limit if requested > 0 else False

        approval_required = (
            action_type in self.ALWAYS_REVIEW
            or irreversible
            or destructive
            or legal
            or exceeds_budget
        )

        approved = bool(action.get("explicit_approval", False))
        return {
            "allowed": (not approval_required) or approved,
            "approval_required": approval_required,
            "reason": (
                "bounded_autonomous_action"
                if not approval_required
                else "explicit_approval_required"
            ),
            "exceeds_budget": exceeds_budget,
        }
