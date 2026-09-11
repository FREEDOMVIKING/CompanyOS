import json
from pathlib import Path
class CompletionStore:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"completed_job_keys.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def load(self):
        if not self.path.exists(): return []
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,list) else []
        except Exception:
            return []

    def add(self, key):
        rows=self.load()
        if key not in rows:
            rows.append(key)
            self.path.write_text(json.dumps(rows,indent=2),encoding="utf-8")
