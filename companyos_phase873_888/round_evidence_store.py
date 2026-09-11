import json
from pathlib import Path
class RoundEvidenceStore:
    """876: persist evidence gathered per revalidation round."""
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"revalidation_round_evidence.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def load(self):
        if not self.path.exists(): return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception:return {}
    def save(self,mission_id,attempt,evidence):
        d=self.load()
        d[f"{mission_id}:{attempt}"]=evidence
        self.path.write_text(json.dumps(d,indent=2,default=str),encoding="utf-8")
        return {"count":len(evidence)}
