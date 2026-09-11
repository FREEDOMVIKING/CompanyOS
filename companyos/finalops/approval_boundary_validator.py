class ApprovalBoundaryValidator:
    GATED={"bank_transfer","contract_signature","production_deploy","large_marketing_spend",
           "hire_employee","borrow_money","legal_filing","acquisition","equity_issuance",
           "public_campaign_launch","delete_external_resource"}
    def validate(self, actions):
        violations=[]
        rows=[]
        for a in actions or []:
            expected=a.get("kind") in self.GATED
            actual=bool(a.get("requires_approval",False))
            passed=expected==actual
            row={**a,"expected_requires_approval":expected,"passed":passed}
            rows.append(row)
            if not passed: violations.append(row)
        return {"passed":not violations,"violations":violations,"actions":rows}
