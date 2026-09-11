from datetime import datetime, timezone, timedelta

class JobLeaseManager:
    def lease(self, job_id, worker_id, seconds=120):
        return {
            "job_id":job_id,
            "worker_id":worker_id,
            "leased_at":datetime.now(timezone.utc).isoformat(),
            "expires_at":(datetime.now(timezone.utc)+timedelta(seconds=int(seconds))).isoformat()
        }
