class ContinuousCEOCycleEngine:
    def cycle(self, queue, departments):
        processed=[]
        for _ in range(max(1,len(departments or []))):
            job=queue.next()
            if not job: break
            dept=(job.get("payload") or {}).get("department") or ((departments or ["operations"])[0])
            result={
                "job_id":job["job_id"],
                "department":dept,
                "status":"complete",
                "task_type":job.get("task_type"),
            }
            queue.complete(job["job_id"],result)
            processed.append(result)
        return {"processed":processed,"count":len(processed)}
