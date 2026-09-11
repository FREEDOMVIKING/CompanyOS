class AuthorityRouter:
    GATED={
        "bank_transfer","contract_signature","production_deploy","large_marketing_spend",
        "hire_employee","borrow_money","legal_filing","acquisition","equity_issuance",
        "public_campaign_launch","delete_external_resource"
    }
    def route(self, actions, autonomous_limit=500):
        auto=[]; approval=[]
        for a in actions or []:
            amount=float(a.get("amount",0) or 0)
            gated=a.get("kind") in self.GATED or amount>float(autonomous_limit)
            row={**a,"allowed":not gated,"requires_approval":gated}
            (approval if gated else auto).append(row)
        return {"autonomous_actions":auto,"approval_queue":approval}
