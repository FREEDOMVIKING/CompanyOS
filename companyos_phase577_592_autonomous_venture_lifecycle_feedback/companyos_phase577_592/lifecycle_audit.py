import json
from datetime import datetime, timezone
from pathlib import Path

class LifecycleAudit:
    """586: append-only lifecycle transition audit."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "venture_lifecycle_audit.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, venture_id, event, payload):
        row = {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "venture_id":venture_id,
            "event":event,
            "payload":payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
