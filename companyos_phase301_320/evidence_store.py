from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

class EvidenceStore:
    """303: append-only evidence storage for discovery research."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "opportunity_evidence.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record):
        row = dict(record)
        row.setdefault("ingested_at", datetime.now(timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row

    def read_recent(self, limit=500):
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines()[-int(limit):]:
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    rows.append(item)
            except Exception:
                pass
        return rows
