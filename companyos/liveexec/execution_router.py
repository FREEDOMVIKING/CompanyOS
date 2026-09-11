class ExecutionRouter:
    def route(self, job, ranked_connectors):
        cap=job.get("capability")
        candidates=[c for c in ranked_connectors or [] if cap in c.get("capabilities",[])]
        return {
            "job_id":job.get("job_id"),
            "selected":candidates[0] if candidates else None,
            "candidates":candidates
        }
