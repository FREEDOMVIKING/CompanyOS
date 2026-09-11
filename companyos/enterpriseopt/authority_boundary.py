class EnterpriseAuthorityBoundary:
    GATED={"venture_retirement","major_capital_reallocation","acquisition","equity_issuance",
           "borrow_money","hire_employee","contract_signature","bank_transfer"}
    def evaluate(self, action):
        gated=action.get("kind") in self.GATED
        return {"allowed_autonomously":not gated,"requires_approval":gated}
