class RestartRecovery:
    """996: resume last safe supercycle stage after restart."""
    def recover(self,state):
        if not state:
            return {"recoverable":False,"stage":"discover"}
        return {
            "recoverable":True,
            "stage":state.get("stage","research"),
            "mission_id":state.get("mission_id"),
            "safe_resume":True,
        }
