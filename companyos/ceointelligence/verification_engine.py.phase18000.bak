class VerificationEngine:
    def verify_execution(self, job, result):
        checks = {
            "job_present": bool(job),
            "result_present": bool(result),
            "execution_success": bool((result or {}).get("success", False)),
        }
        return {
            "passed": all(checks.values()),
            "checks": checks,
            "job_id": (job or {}).get("job_id")
        }

    def summarize_cycle(self, results):
        passed = sum(1 for r in results if r.get("verification", {}).get("passed"))
        failed = len(results) - passed
        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "cycle_verified": failed == 0 and len(results) > 0
        }
