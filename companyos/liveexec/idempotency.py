import json
from pathlib import Path

class IdempotencyStore:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"liveexec_idempotency.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def load(self):
        if not self.path.exists(): return {}
        try:return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:return {}

    def seen(self,key):
        return bool(key and key in self.load())

    def record(self,key,result):
        if not key: return
        d=self.load()
        d[key]=result
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")

    def get(self,key):
        return self.load().get(key)
