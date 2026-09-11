class DelegatedBudget:
    """692: bounded authority envelope by action category."""

    def evaluate(self, action, limits=None):
        limits = limits or {
            "max_internal_compute_units":1000,
            "max_external_messages":0,
            "max_financial_commitment_usd":0,
        }
        requested = float(action.get("financial_commitment_usd",0))
        return {
            "within_budget": requested <= float(limits.get("max_financial_commitment_usd",0)),
            "requested_financial_commitment_usd": requested,
            "limits": limits,
        }
