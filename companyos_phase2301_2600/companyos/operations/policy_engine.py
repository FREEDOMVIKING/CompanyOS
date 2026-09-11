class OperatingPolicyEngine:
    GATED={"contract_signature","bank_transfer","production_deploy","large_marketing_spend",
           "hire_employee","borrow_money","legal_filing","acquisition"}

    def evaluate(self, actions, amount_limit=500):
        auto=[]; gated=[]
        for a in actions or []:
            amount=float(a.get("amount",0) or 0)
            needs=a.get("kind") in self.GATED or amount>float(amount_limit)
            row={**a,"requires_approval":needs}
            (gated if needs else auto).append(row)
        return {"autonomous":auto,"approval_queue":gated}
