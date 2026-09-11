class RuntimeGuardrails:
    GATED={"bank_transfer","contract_signature","production_deploy","large_spend","hire_employee",
           "borrow_money","legal_filing","acquisition","delete_external_resource"}

    def evaluate(self, action, amount_limit=500):
        amount=float(action.get("amount",0) or 0)
        gated=action.get("kind") in self.GATED or amount>float(amount_limit)
        return {"allowed":not gated,"requires_approval":gated,
                "reason":"explicit_approval_required" if gated else "within_runtime_authority"}
