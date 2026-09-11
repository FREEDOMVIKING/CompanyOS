import json
from pathlib import Path
class RevalidationHistoryStore:
    """891: persistent confidence/decision history."""
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"multi_round_revalidation_history.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def load(self):
        if not self.path.exists(): return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception: return {}
    def append(self,key,row):
        d=self.load(); h=list(d.get(str(key),[])); h.append(row); d[str(key)]=h
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")
        return h
