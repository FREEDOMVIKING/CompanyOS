class ResilienceAuthorityBoundary:
    GATED={
        "destroy_primary_data","disable_audit","bypass_approval",
        "rotate_financial_credentials","irreversible_external_shutdown"
    }
    def evaluate(self, action):
        gated=action.get("kind") in self.GATED
        return {"allowed_autonomously":not gated,"requires_approval":gated}
