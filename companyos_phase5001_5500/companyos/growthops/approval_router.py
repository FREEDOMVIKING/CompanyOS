class GrowthApprovalRouter:
    GATED={"large_marketing_spend","contract_signature","production_deploy","bank_transfer","public_campaign_launch"}
    def route(self, actions, autonomous_limit=500):
        autonomous=[]; approval=[]
        for a in actions or []:
            gated=a.get("kind") in self.GATED or float(a.get("amount",0) or 0)>autonomous_limit
            row={**a,"allowed":not gated,"requires_approval":gated}
            (approval if gated else autonomous).append(row)
        return {"autonomous_actions":autonomous,"approval_queue":approval}
