from .authority_matrix import AuthorityMatrix
from .risk_classifier import RiskClassifier

class ApprovalGateway:
    """691: centralized approval decision."""

    def evaluate(self, action):
        authority = AuthorityMatrix().classify(action.get("action_type"))
        risk = RiskClassifier().classify(action)
        approval = authority != "autonomous" or risk in ("high","irreversible")
        return {
            "approval_required": approval,
            "authority": authority,
            "risk": risk,
            "reason": "sensitive_or_high_impact_action" if approval else "within_delegated_autonomy",
        }
