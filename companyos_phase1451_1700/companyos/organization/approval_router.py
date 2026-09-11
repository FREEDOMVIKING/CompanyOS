class ApprovalRouter:
    HIGH_RISK={"contract_signature","bank_transfer","large_spend","hire_employee","borrow_money",
               "production_delete","legal_filing","external_account_creation","acquisition"}

    def route(self, actions, autonomous_amount_limit=500):
        auto=[]; approval=[]
        for a in actions or []:
            amount=float(a.get("amount",0) or 0)
            gated=a.get("kind") in self.HIGH_RISK or amount>float(autonomous_amount_limit)
            row={**a,"requires_approval":gated}
            (approval if gated else auto).append(row)
        return {"autonomous":auto,"approval_queue":approval}
