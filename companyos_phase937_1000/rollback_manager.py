class RollbackManager:
    """989-992: automatic rollback plan/result."""
    def plan(self, artifact_ref=None, previous_ref=None):
        return {
            "rollback_ready": bool(previous_ref or artifact_ref),
            "artifact_ref": artifact_ref,
            "previous_ref": previous_ref,
            "steps": ["stop new release","restore previous artifact/config","verify health","resume traffic"],
        }
