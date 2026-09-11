import json
from pathlib import Path
class ResearchRetryState:
    """770: persistent retry accounting by mission/provider."""
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"research_retry_state.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def load(self):
        if not self.path.exists(): return {}
        try:
            x=json.loads(self.path.read_text(encoding="utf-8"))
            return x if isinstance(x,dict) else {}
        except Exception: return {}
    def increment(self,mission_id,provider):
        d=self.load(); key=f"{mission_id}:{provider}"
        d[key]=int(d.get(key,0))+1
        self.path.write_text(json.dumps(d,indent=2),encoding="utf-8")
        return d[key]
