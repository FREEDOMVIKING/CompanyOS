class ProductionRecoveryManager:
    def plan(self, checkpoint, failures):
        actions=[]
        for f in failures or []:
            kind=f.get("kind")
            action={
                "worker_crash":"restart_and_requeue",
                "provider_failure":"failover_provider",
                "queue_stall":"restart_queue_worker",
                "state_corruption":"restore_checkpoint",
                "service_failure":"restart_service"
            }.get(kind,"safe_diagnose")
            actions.append({**f,"recovery_action":action})
        return {
            "checkpoint_available":bool(checkpoint),
            "actions":actions,
            "recoverable":bool(checkpoint) or not failures
        }
