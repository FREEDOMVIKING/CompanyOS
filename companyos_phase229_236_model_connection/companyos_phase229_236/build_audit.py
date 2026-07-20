from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

class BuildAudit:
    """234: append-only audit log for autonomous self-build missions."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "selfbuild_audit.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event, payload):
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\\n")
        return row
