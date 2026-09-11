class RestartRecovery:
    def plan(self, state, jobs):
        recover=[j for j in jobs or [] if j.get("status") in ("running","retry","queued")]
        return {
            "checkpoint_present": bool(state),
            "recoverable_jobs": recover,
            "action": "resume_from_checkpoint" if state else "cold_start"
        }
