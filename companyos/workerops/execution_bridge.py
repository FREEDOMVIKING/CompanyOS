class ExecutionBridge:
    def __init__(self, root=None):
        self.root = root

    def execute(self, job, department):
        specialist_result = None

        if self.root:
            try:
                from companyos.specialistops import SpecialistCapabilityRouter
                router = SpecialistCapabilityRouter(self.root)
                if router.supports(department):
                    specialist_result = router.execute(job, department)
                    if specialist_result.get("success"):
                        return specialist_result
            except Exception as exc:
                specialist_result = {
                    "success": False,
                    "error": "specialist_execution_failure",
                    "message": str(exc)
                }

            try:
                from companyos.capabilityops import RealExecutionBridge
                real_result = RealExecutionBridge(self.root).execute(job, department)
                if real_result.get("success"):
                    return real_result
            except Exception as exc:
                real_result = {
                    "success": False,
                    "error": "real_execution_bridge_failure",
                    "message": str(exc)
                }

            try:
                from companyos.failureops import RecoveryRouter
                base_result = specialist_result if specialist_result else real_result
                recovery = RecoveryRouter(self.root).recover(job, department, base_result)
                if recovery.get("recovered"):
                    return recovery["result"]
                return recovery.get("result") or base_result
            except Exception as exc:
                return {
                    "success": False,
                    "error": "recovery_router_failure",
                    "message": str(exc),
                    "job_id": job.get("job_id"),
                    "department": department
                }

        return {
            "success": True,
            "job_id": job.get("job_id"),
            "department": department,
            "kind": job.get("kind"),
            "mode": "internal_fallback",
            "result": "internal_execution_complete"
        }
