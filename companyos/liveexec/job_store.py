import json
from pathlib import Path

class PersistentJobStore:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"liveexec_jobs.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def load(self):
        if not self.path.exists(): return []
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,list) else []
        except Exception:return []

    def save(self,rows):
        self.path.write_text(json.dumps(rows,indent=2,default=str),encoding="utf-8")

    def add(self,job):
        rows=self.load(); rows.append(job); self.save(rows); return job

    def update(self,job_id,**fields):
        rows=self.load()
        for r in rows:
            if r.get("job_id")==job_id:r.update(fields)
        self.save(rows)

    def pending(self):
        return [r for r in self.load() if r.get("status") in ("queued","retry")]
