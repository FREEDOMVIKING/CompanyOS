class DeepRecoveryCoordinator:
    def plan(self, failures):
        actions=[]
        for f in failures or []:
            kind=f.get("kind")
            action={
                "worker_crash":"requeue_job_and_restart_worker",
                "workflow_stall":"restore_workflow_checkpoint",
                "queue_corruption":"restore_queue_snapshot",
                "provider_failure":"switch_provider",
                "resource_exhaustion":"reduce_parallelism",
            }.get(kind,"safe_diagnose")
            actions.append({**f,"recovery_action":action})
        return actions
