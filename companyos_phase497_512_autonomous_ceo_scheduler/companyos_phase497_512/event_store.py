import json
from datetime import datetime, timezone
from pathlib import Path

class EventStore:
    """500: append-only CEO scheduler event stream."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "ceo_scheduler_events.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type, payload=None):
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload or {},
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
