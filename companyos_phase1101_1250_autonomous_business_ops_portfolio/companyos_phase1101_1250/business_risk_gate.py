class BusinessRiskGate:
    """1241-1246: explicit limits for high-risk financial/external business actions."""
    HIGH_RISK={"large_marketing_spend","contract_signature","hire_employee","borrow_money","large_vendor_commitment","acquisition"}

    def evaluate(self, action, amount=0, autonomous_limit=500):
        high=action in self.HIGH_RISK or float(amount)>float(autonomous_limit)
        return {
            "action":action,
            "amount":float(amount),
            "requires_approval":high,
            "auto_allowed":not high,
            "reason":"human_approval_required" if high else "within_autonomous_business_limits"
        }
