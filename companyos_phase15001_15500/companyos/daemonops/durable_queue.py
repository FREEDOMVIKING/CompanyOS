import json, uuid
from pathlib import Path
from datetime import datetime, timezone

class DurableJobQueue:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"daemon_jobs.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return []
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d, list) else []
        except Exception:
            return []

    def save(self, rows):
        self.path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")

    def enqueue(self, kind, payload=None, priority=5):
        rows = self.load()
        row = {
            "job_id": "job_" + uuid.uuid4().hex[:12],
            "kind": kind,
            "payload": payload or {},
            "priority": int(priority),
            "status": "queued",
            "attempts": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        rows.append(row)
        self.save(rows)
        return row

    def next_job(self):
        rows = [r for r in self.load() if r.get("status") in ("queued","retry")]
        rows.sort(key=lambda x: (-int(x.get("priority",0)), x.get("created_at","")))
        return rows[0] if rows else None

    def update(self, job_id, **fields):
        rows = self.load()
        for r in rows:
            if r.get("job_id") == job_id:
                r.update(fields)
        self.save(rows)
