class ControlledAutonomyPolicy:
    def decide(self, action):
        impact = str(action.get("impact","low")).lower()
        reversible = bool(action.get("reversible", True))
        moves_money = bool(action.get("moves_money", False))
        changes_credentials = bool(action.get("changes_credentials", False))
        deploys_production = bool(action.get("deploys_production", False))
        within_treasury_policy = bool(action.get("within_treasury_policy", False))

        if changes_credentials:
            return {"decision":"approval_required","reason":"credential_change"}

        if moves_money and not within_treasury_policy:
            return {"decision":"blocked","reason":"treasury_policy_not_satisfied"}

        if not reversible:
            return {"decision":"approval_required","reason":"irreversible_action"}

        if deploys_production and impact in {"high","critical"}:
            return {"decision":"approval_required","reason":"high_impact_production_change"}

        if impact == "critical":
            return {"decision":"approval_required","reason":"critical_impact"}

        return {"decision":"autonomous_allowed","reason":"bounded_reversible_action"}
