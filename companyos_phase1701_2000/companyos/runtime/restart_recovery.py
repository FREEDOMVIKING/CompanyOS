class RestartSafeRecovery:
    def recover(self, checkpoint, queue_snapshot):
        if not checkpoint:
            return {"recoverable":False,"action":"start_clean_cycle"}
        running=int((queue_snapshot or {}).get("running",0))
        return {
            "recoverable":True,
            "action":"resume_from_checkpoint",
            "requeue_inflight":running>0,
            "checkpoint_state":checkpoint.get("state",{}),
        }
