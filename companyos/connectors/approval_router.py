class ConnectorApprovalRouter:
    GATED={
        "send_external_message","production_deploy","bank_transfer","contract_signature",
        "large_marketing_spend","public_campaign_launch","create_external_account",
        "delete_external_resource","legal_filing","borrow_money","hire_employee"
    }

    def route(self, actions, amount_limit=500):
        auto=[]; approval=[]
        for a in actions or []:
            amount=float(a.get("amount",0) or 0)
            gated=a.get("kind") in self.GATED or amount>float(amount_limit)
            row={**a,"allowed":not gated,"requires_approval":gated}
            (approval if gated else auto).append(row)
        return {"autonomous_actions":auto,"approval_queue":approval}
