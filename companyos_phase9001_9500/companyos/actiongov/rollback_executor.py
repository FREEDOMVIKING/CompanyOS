class RollbackExecutor:
    def plan(self, action):
        reversible=bool(action.get("reversible",False))
        return {
            "reversible":reversible,
            "steps":["pause_related_work","restore_previous_state","verify","resume"] if reversible else [],
            "ready":reversible
        }
