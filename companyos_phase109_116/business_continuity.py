class BusinessContinuity:
    """114: continuity plans for degraded dependencies."""
    def plan(self,dependencies):
        actions=[]
        for d in dependencies:
            if not bool(d.get("healthy",True)):
                actions.append({"dependency":d.get("name"),"action":"activate_fallback" if d.get("fallback") else "degrade_and_escalate",
                "destructive_action":False})
        return {"degraded":bool(actions),"actions":actions}
