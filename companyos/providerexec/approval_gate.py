class ProviderApprovalGate:
    GATED={"send_external_message","production_deploy","bank_transfer","contract_signature",
           "large_marketing_spend","public_campaign_launch","legal_filing","borrow_money",
           "hire_employee","delete_external_resource"}

    def evaluate(self, action, amount_limit=500):
        amount=float(action.get("amount",0) or 0)
        gated=action.get("kind") in self.GATED or amount>float(amount_limit)
        return {
            "allowed":not gated,
            "requires_approval":gated,
            "reason":"explicit_approval_required" if gated else "within_provider_execution_authority"
        }
