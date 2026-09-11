class RevenueAuthorityBoundary:
    GATED={"charge_customer","issue_refund","sign_sales_contract","large_ad_spend","change_billing_terms","send_external_campaign"}
    def evaluate(self, action):
        gated=action.get("kind") in self.GATED
        return {"allowed_autonomously":not gated,"requires_approval":gated}
