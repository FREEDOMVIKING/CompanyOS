class AutonomyGovernor:
    def classify(self, action):
        irreversible=bool(action.get("irreversible",False))
        external=bool(action.get("external",False))
        moves_money=bool(action.get("moves_money",False))
        within_policy=bool(action.get("within_policy",False))
        if irreversible:
            return {"decision":"approval_required","reason":"irreversible_action"}
        if moves_money and not within_policy:
            return {"decision":"blocked","reason":"treasury_policy_not_satisfied"}
        if external and action.get("requires_external_approval",True):
            return {"decision":"approval_required","reason":"external_action_gate"}
        return {"decision":"autonomous_allowed","reason":"reversible_or_policy_authorized"}
