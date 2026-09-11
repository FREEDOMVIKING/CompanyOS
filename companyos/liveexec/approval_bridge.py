class ApprovalExecutionBridge:
    GATED={"send_external_message","production_deploy","bank_transfer","contract_signature",
           "large_marketing_spend","public_campaign_launch","legal_filing","borrow_money",
           "hire_employee","delete_external_resource"}

    def split(self,jobs):
        autonomous=[]; approval=[]
        for j in jobs or []:
            gated=j.get("action") in self.GATED
            row={**j,"requires_approval":gated}
            (approval if gated else autonomous).append(row)
        return {"autonomous_jobs":autonomous,"approval_jobs":approval}
