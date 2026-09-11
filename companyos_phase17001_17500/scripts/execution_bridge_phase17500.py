class ExecutionBridge:
    def __init__(self, root=None):
        self.root = root

    def execute(self, job, department):
        specialist_failure = None

        if self.root:
            try:
                from companyos.specialistops import SpecialistCapabilityRouter
                router = SpecialistCapabilityRouter(self.root)
                if router.supports(department):
                    result = router.execute(job, department)
                    if result.get("success"):
                        return result
                    specialist_failure = result
            except Exception as exc:
                specialist_failure = {
                    "success": False,
                    "error": "specialist_execution_failure",
                    "message": str(exc),
                    "department": department,
                    "job_id": job.get("job_id")
                }

            try:
                from companyos.capabilityops import RealExecutionBridge
                result = RealExecutionBridge(self.root).execute(job, department)
                if specialist_failure:
                    result["specialist_failure"] = specialist_failure
                return result
            except Exception as exc:
                if specialist_failure:
                    return specialist_failure
                return {
                    "success": False,
                    "job_id": job.get("job_id"),
                    "department": department,
                    "kind": job.get("kind"),
                    "error": "real_execution_bridge_failure",
                    "message": str(exc)
                }

        return {
            "success": True,
            "job_id": job.get("job_id"),
            "department": department,
            "kind": job.get("kind"),
            "mode": "internal_fallback",
            "result": "internal_execution_complete"
        }
