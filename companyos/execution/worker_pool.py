import json
from pathlib import Path

class PersistentWorkerPool:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"worker_pool.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def load(self):
        if not self.path.exists(): return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception:return {}

    def ensure(self, workers):
        d=self.load()
        for w in workers or []:
            wid=w["worker_id"]
            d[wid]={**w,"status":w.get("status","idle"),"jobs_completed":int(w.get("jobs_completed",0))}
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")
        return d

    def available(self, capability=None):
        rows=[x for x in self.load().values() if x.get("status")=="idle"]
        if capability:
            rows=[x for x in rows if capability in x.get("capabilities",[])]
        return rows
