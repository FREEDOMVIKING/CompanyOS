class ExpansionAuthorityBoundary:
    GATED={
        "enter_new_country","form_legal_entity","sign_partner_agreement","major_capital_commitment",
        "acquisition","hire_employee","borrow_money","bank_transfer","contract_signature"
    }
    def evaluate(self, action):
        gated=action.get("kind") in self.GATED
        return {"allowed_autonomously":not gated,"requires_approval":gated}
