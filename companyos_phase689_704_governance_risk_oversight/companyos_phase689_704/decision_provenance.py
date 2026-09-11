from datetime import datetime, timezone

class DecisionProvenance:
    """702: record why governance allowed/rejected an action."""

    def build(self, action, preflight, violation):
        return {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "action_type":action.get("action_type"),
            "allowed":bool(preflight.get("allowed_to_execute")) and not violation.get("violation"),
            "approval_required":preflight.get("approval",{}).get("approval_required"),
            "risk":preflight.get("approval",{}).get("risk"),
            "reasons":violation.get("reasons",[]),
        }
