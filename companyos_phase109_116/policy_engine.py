class PolicyEngine:
    """112: central bounded-authority policy evaluation."""
    def evaluate(self,action):
        external=bool(action.get("external",False));financial=bool(action.get("financial",False))
        irreversible=bool(action.get("irreversible",False));approved=bool(action.get("explicit_approval",False))
        approval_required=financial or irreversible or bool(action.get("approval_required",False))
        return {"approval_required":approval_required,"allowed":(not approval_required) or approved,
        "external":external,"financial":financial,"irreversible":irreversible}
