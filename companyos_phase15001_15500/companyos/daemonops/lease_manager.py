class JobLeaseManager:
    def acquire(self, job, worker, tick, ttl=3):
        return {
            "job_id": job.get("job_id"),
            "worker": worker,
            "lease_start_tick": int(tick),
            "lease_expiry_tick": int(tick)+int(ttl)
        }

    def expired(self, lease, tick):
        return int(tick) > int(lease.get("lease_expiry_tick",0))
