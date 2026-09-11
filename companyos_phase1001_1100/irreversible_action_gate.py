class IrreversibleActionGate:
    """1015-1020: explicit gate for financially/materially irreversible actions."""
    HIGH_RISK={"production_traffic_cutover","external_spend","contract_commitment","delete_production_data","large_financial_transfer"}

    def evaluate(self, action, context=None):
        context=context or {}
        risk="high" if action in self.HIGH_RISK else context.get("risk","low")
        requires_approval = risk=="high"
        return {
            "action":action,
            "risk":risk,
            "requires_approval":requires_approval,
            "auto_allowed":not requires_approval,
            "reason":"explicit_human_approval_required" if requires_approval else "reversible_or_low_risk",
        }
