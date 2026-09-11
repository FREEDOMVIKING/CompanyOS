import hashlib, json
class JobDedupeEngine:
    def key(self, job):
        payload={"kind":job.get("kind"),"payload":job.get("payload")}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()

    def is_duplicate(self, job, completed_keys):
        return self.key(job) in set(completed_keys or [])
