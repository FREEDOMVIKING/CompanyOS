import json
from pathlib import Path
from datetime import datetime, timezone

class CycleStateStore:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"autonomous_company_cycle.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def load(self):
        if not self.path.exists():
            return {"cycle":0,"history":[],"last_status":"never_run"}
        try: return json.loads(self.path.read_text())
        except Exception: return {"cycle":0,"history":[],"last_status":"state_recovered"}
    def save(self,state):
        state["updated_at"]=datetime.now(timezone.utc).isoformat()
        self.path.write_text(json.dumps(state,indent=2))
        return state
