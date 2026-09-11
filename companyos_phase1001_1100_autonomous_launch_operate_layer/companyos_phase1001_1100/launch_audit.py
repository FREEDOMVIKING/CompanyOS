import json
from pathlib import Path
from datetime import datetime,timezone

class LaunchAudit:
    """1089-1092: append-only launch and operations audit."""
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"launch_operate_audit.jsonl"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def append(self,payload):
        row={"timestamp":datetime.now(timezone.utc).isoformat(),**payload}
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,default=str)+"\n")
        return row
