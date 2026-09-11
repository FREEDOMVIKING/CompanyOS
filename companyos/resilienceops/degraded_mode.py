class DegradedModePlanner:
    def plan(self, failed_capabilities):
        failed=set(failed_capabilities or [])
        return {
            "mode":"degraded" if failed else "normal",
            "disable_nonessential":bool(failed),
            "preserve":[
                "state_integrity","approval_boundaries","audit",
                "checkpointing","health_monitoring"
            ],
            "failed_capabilities":sorted(failed)
        }
