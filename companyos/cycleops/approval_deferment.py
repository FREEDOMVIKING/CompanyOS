class ApprovalDeferment:
    def normalize(self, job, execution):
        job = job or {}
        execution = execution or {}
        payload = job.get("payload") or {}
        requires = bool(
            payload.get("requires_approval")
            or job.get("requires_approval")
            or execution.get("requires_approval")
        )
        if requires and execution.get("success") is not True:
            return {
                "success": False,
                "blocked": True,
                "reason": "approval_required",
                "requires_approval": True,
                "resolution_state": "deferred_for_approval",
                "job_id": job.get("job_id")
            }
        return execution
