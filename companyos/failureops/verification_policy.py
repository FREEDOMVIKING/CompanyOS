class VerificationPolicy:
    def verify(self, job, execution):
        result = execution or {}
        checks = {
            "job_present": bool(job),
            "result_present": bool(result),
            "success_flag": bool(result.get("success")),
            "not_approval_blocked": not bool(result.get("blocked")),
        }
        capability = result.get("capability")
        if capability:
            checks["capability_present"] = True
        return {
            "passed": all(checks.values()),
            "checks": checks,
            "job_id": (job or {}).get("job_id")
        }
