class RestartSafeRuntime:
    def recover(self, checkpoint, inflight=None):
        return {
            "recoverable":bool(checkpoint),
            "action":"resume_from_checkpoint" if checkpoint else "cold_start",
            "requeue_inflight":bool(inflight),
            "inflight_count":len(inflight or [])
        }
