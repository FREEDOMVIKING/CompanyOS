import json
from pathlib import Path
from datetime import datetime, timezone
class GovernanceState:
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"governance_state.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def save(self,state):
        row={"timestamp":datetime.now(timezone.utc).isoformat(),"state":state}
        self.path.write_text(json.dumps(row,indent=2,default=str),encoding="utf-8")
        return row
