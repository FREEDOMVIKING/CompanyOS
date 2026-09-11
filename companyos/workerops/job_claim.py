class JobClaimEngine:
    def claim(self, job, worker_id, tick=0, lease_ticks=3):
        if not job:
            return None
        if job.get("status") not in ("queued","retry"):
            return None
        return {
            **job,
            "status":"running",
            "claimed_by":worker_id,
            "lease_start_tick":int(tick),
            "lease_expiry_tick":int(tick)+int(lease_ticks),
            "attempts":int(job.get("attempts",0))+1
        }
