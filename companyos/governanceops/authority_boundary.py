class GovernanceAuthorityBoundary:
    GATED={
        "weaken_security_control","disable_audit","delete_required_records",
        "approve_policy_exception","expand_financial_authority","bypass_approval"
    }
    def evaluate(self,action):
        gated=action.get("kind") in self.GATED
        return {"allowed_autonomously":not gated,"requires_approval":gated}
