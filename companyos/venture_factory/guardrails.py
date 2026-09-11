class VentureGuardrails:
    GATED={"production_deploy","bank_transfer","contract_signature","large_marketing_spend",
           "hire_employee","borrow_money","legal_filing","acquisition"}
    def route(self, actions):
        autonomous=[]; approval=[]
        for a in actions or []:
            requires=a.get("kind") in self.GATED
            row={**a,"allowed":not requires,"requires_approval":requires}
            (approval if requires else autonomous).append(row)
        return {"autonomous":autonomous,"approval_queue":approval}
