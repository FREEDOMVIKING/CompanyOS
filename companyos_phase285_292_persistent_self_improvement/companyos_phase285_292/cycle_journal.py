from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

class CycleJournal:
    """286: append-only persistent improvement journal."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "persistent_cycle_journal.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event, payload):
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
