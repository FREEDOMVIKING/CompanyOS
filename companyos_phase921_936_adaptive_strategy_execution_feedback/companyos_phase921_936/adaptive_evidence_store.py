import json
from pathlib import Path
class AdaptiveEvidenceStore:
    """926: persist adaptive evidence by mission and strategy round."""
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"adaptive_research_evidence.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def load(self):
        if not self.path.exists(): return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception:return {}
    def save(self,key,round_no,evidence):
        d=self.load()
        d[f"{key}:{round_no}"]=evidence
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")
        return {"count":len(evidence)}
