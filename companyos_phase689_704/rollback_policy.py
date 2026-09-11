class RollbackPolicy:
    """698: rollback requirements for autonomous changes."""

    def evaluate(self, action):
        mutating = bool(action.get("mutates_state"))
        reversible = bool(action.get("reversible",False))
        return {
            "rollback_required": mutating,
            "rollback_ready": (not mutating) or reversible,
            "autonomous_execution_allowed": (not mutating) or reversible,
        }
