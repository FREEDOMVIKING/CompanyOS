import json
from datetime import datetime, timezone
from pathlib import Path

class ServiceJournal:
    """553: append-only continuous-service journal."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "ceo_service_journal.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event, payload=None):
        row = {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "event":event,
            "payload":payload or {},
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
