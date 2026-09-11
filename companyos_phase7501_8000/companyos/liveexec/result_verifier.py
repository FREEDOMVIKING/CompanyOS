class LiveResultVerifier:
    def verify(self, job, result, required_fields=None):
        missing=[]
        payload=(result or {}).get("result",{})
        for f in required_fields or []:
            if f not in payload:
                missing.append(f)
        success=bool((result or {}).get("success")) and not missing
        return {"verified":success,"missing_fields":missing,"job_id":job.get("job_id")}
