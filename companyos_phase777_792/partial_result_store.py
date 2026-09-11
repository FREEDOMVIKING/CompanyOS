import json
from pathlib import Path
class PartialResultStore:
    """788: preserve partial evidence between failover attempts."""
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"partial_research_results.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def load(self):
        if not self.path.exists(): return {}
        try:
            x=json.loads(self.path.read_text(encoding="utf-8"))
            return x if isinstance(x,dict) else {}
        except Exception: return {}
    def save(self,mission_id,evidence):
        d=self.load(); d[mission_id]=evidence
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")
        return {"mission_id":mission_id,"evidence_count":len(evidence)}
