import json
from pathlib import Path
from datetime import datetime, timezone

class ExecutionAudit:
    """571: append-only venture execution audit."""

    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"business_execution_audit.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event, payload):
        row={
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "event":event,
            "payload":payload,
        }
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,default=str)+"\n")
        return row
