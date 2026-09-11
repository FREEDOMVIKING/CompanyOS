class RestartCoordinator:
    def plan(self, checkpoint, health):
        if not checkpoint:
            return {"action":"cold_start","recoverable":False}
        if (health or {}).get("healthy",False):
            return {"action":"resume","recoverable":True}
        return {"action":"safe_recovery_resume","recoverable":True,"health_actions":(health or {}).get("actions",[])}
