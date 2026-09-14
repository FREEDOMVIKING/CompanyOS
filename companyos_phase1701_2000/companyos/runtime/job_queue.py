import json, uuid
from pathlib import Path
from datetime import datetime, timezone

class PersistentJobQueue:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"persistent_job_queue.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if not self.path.exists(): return []
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,list) else []
        except Exception:
            return []

    def _save(self, rows):
        self.path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")

    def enqueue(self, task_type, payload=None, priority=5):
        rows=self._load()
        row={
            "job_id":"job_"+uuid.uuid4().hex[:12],
            "task_type":task_type,
            "payload":payload or {},
            "priority":int(priority),
            "status":"queued",
            "attempts":0,
            "created_at":datetime.now(timezone.utc).isoformat()
        }
        rows.append(row)
        self._save(rows)
        return row

    def next(self):
        rows=self._load()
        queued=[r for r in rows if r.get("status")=="queued"]
        if not queued: return None
        queued.sort(key=lambda r:(-int(r.get("priority",0)), r.get("created_at","")))
        chosen=queued[0]
        for r in rows:
            if r.get("job_id")==chosen.get("job_id"):
                r["status"]="running"; r["attempts"]=int(r.get("attempts",0))+1
                chosen=dict(r); break
        self._save(rows)
        return chosen

    def complete(self, job_id, result=None):
        rows=self._load()
        for r in rows:
            if r.get("job_id")==job_id:
                r["status"]="complete"; r["result"]=result or {}
        self._save(rows)

    def fail(self, job_id, error, retry=True, max_attempts=3):
        rows=self._load()
        for r in rows:
            if r.get("job_id")==job_id:
                r["last_error"]=str(error)
                if retry and int(r.get("attempts",0)) < int(max_attempts):
                    r["status"]="queued"
                else:
                    r["status"]="failed"
        self._save(rows)

    def snapshot(self):
        rows=self._load()
        return {
            "total":len(rows),
            "queued":sum(1 for r in rows if r.get("status")=="queued"),
            "running":sum(1 for r in rows if r.get("status")=="running"),
            "complete":sum(1 for r in rows if r.get("status")=="complete"),
            "failed":sum(1 for r in rows if r.get("status")=="failed"),
        }
