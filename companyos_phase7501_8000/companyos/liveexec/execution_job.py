import uuid
from datetime import datetime, timezone

class ExecutionJob:
    def create(self, capability, action, payload=None, priority=5, idempotency_key=None):
        return {
            "job_id":"livejob_"+uuid.uuid4().hex[:12],
            "capability":capability,
            "action":action,
            "payload":payload or {},
            "priority":int(priority),
            "idempotency_key":idempotency_key,
            "status":"queued",
            "created_at":datetime.now(timezone.utc).isoformat()
        }
