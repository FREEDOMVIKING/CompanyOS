class SafePatchGenerator:
    def propose(self, component, change, reversible=True):
        return {
            "component":component,
            "change":change,
            "reversible":bool(reversible),
            "status":"proposal_only",
            "requires_validation":True
        }
