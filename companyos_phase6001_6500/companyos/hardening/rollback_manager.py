class RollbackManager:
    def plan(self, release):
        return {
            "release":release,
            "steps":["stop_new_work","snapshot_state","restore_previous_artifact","restore_config","run_health_checks","resume"],
            "ready":bool((release or {}).get("previous_artifact"))
        }
