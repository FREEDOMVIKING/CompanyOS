class ActionPolicyEngine:
    APPROVAL_REQUIRED={
        "bank_transfer","contract_signature","production_deploy","large_marketing_spend",
        "public_campaign_launch","legal_filing","borrow_money","hire_employee",
        "delete_external_resource","equity_issuance","acquisition"
    }
    def evaluate(self, action, autonomous_amount_limit=500):
        amount=float(action.get("amount",0) or 0)
        kind=action.get("kind","")
        requires=kind in self.APPROVAL_REQUIRED or amount>float(autonomous_amount_limit)
        return {
            "kind":kind,
            "requires_approval":requires,
            "allowed_autonomously":not requires,
            "reason":"approval_policy" if requires else "within_autonomous_policy"
        }
