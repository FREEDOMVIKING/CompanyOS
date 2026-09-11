class RetryPolicy:
    def decide(self, job, result, max_attempts=3):
        attempts=int(job.get("attempts",0))
        if result.get("success"):
            return {"action":"complete"}
        if attempts < int(max_attempts):
            return {"action":"retry"}
        return {"action":"dead_letter"}
