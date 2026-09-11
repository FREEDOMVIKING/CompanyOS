class PersistentFailureRecovery:
    def plan(self, failures):
        out=[]
        for f in failures or []:
            kind=f.get("kind","unknown")
            action={
                "provider_failure":"switch_provider",
                "agent_failure":"reassign_task",
                "queue_stall":"restart_worker",
                "memory_corruption":"restore_checkpoint",
                "budget_overrun":"freeze_nonessential_spend",
            }.get(kind,"safe_diagnose")
            out.append({**f,"recovery_action":action})
        return out
