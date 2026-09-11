class ProductAuthorityBoundary:
    GATED={
        "production_deploy","sunset_product","change_customer_contract_behavior",
        "collect_new_sensitive_data","public_launch","major_vendor_commitment"
    }
    def evaluate(self, action):
        gated=action.get("kind") in self.GATED
        return {"allowed_autonomously":not gated,"requires_approval":gated}
