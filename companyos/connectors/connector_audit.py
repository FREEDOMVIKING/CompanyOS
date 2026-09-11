import json
from pathlib import Path
from datetime import datetime, timezone

class ConnectorAudit:
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"connector_layer_audit.jsonl"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def append(self,event,payload):
        row={"timestamp":datetime.now(timezone.utc).isoformat(),"event":event,"payload":payload}
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,default=str)+"\n")
        return row
