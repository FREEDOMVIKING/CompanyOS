class CustomerAuthorityBoundary:
    GATED={"issue_refund","offer_financial_credit","change_contract","terminate_customer","send_legal_response","disclose_sensitive_data"}
    def evaluate(self, action):
        gated=action.get("kind") in self.GATED
        return {"allowed_autonomously":not gated,"requires_approval":gated}
