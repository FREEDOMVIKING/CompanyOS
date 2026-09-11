from .approval_gateway import ApprovalGateway
from .delegated_budget import DelegatedBudget
from .financial_exposure import FinancialExposure
from .external_action_policy import ExternalActionPolicy

class PreflightCheck:
    """697: pre-action governance simulation."""

    def run(self, action, limits=None):
        approval = ApprovalGateway().evaluate(action)
        budget = DelegatedBudget().evaluate(action, limits)
        finance = FinancialExposure().evaluate(action)
        external = ExternalActionPolicy().evaluate(action)
        allowed = (not approval["approval_required"]) and budget["within_budget"]
        return {
            "allowed_to_execute": allowed,
            "approval": approval,
            "budget": budget,
            "financial_exposure": finance,
            "external_policy": external,
        }
