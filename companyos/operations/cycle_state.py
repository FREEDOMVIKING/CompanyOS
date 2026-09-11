import json
from pathlib import Path
from datetime import datetime, timezone

class ContinuousCycleState:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"continuous_operations_state.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def save(self, state):
        row={"timestamp":datetime.now(timezone.utc).isoformat(),"state":state}
        self.path.write_text(json.dumps(row,indent=2,default=str),encoding="utf-8")
        return row

    def load(self):
        if not self.path.exists(): return {}
        try:return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:return {}
