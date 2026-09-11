class RollbackCoordinator:
    def plan(self, change):
        return {
            "change":change,
            "steps":["pause_new_work","capture_current_state","restore_previous_version","verify_health","resume"],
            "ready":bool(change.get("previous_version"))
        }
