class SelfImprovementBoundary:
    GATED={"safety_policy","financial_authority","external_action_policy","credential_scope","approval_bypass"}
    def evaluate(self, change):
        kind=change.get("kind")
        gated=kind in self.GATED
        return {
            "allowed_autonomously":not gated,
            "requires_approval":gated,
            "reason":"protected_boundary" if gated else "internal_reversible_improvement"
        }
