import json
from datetime import datetime, timezone
from pathlib import Path

class ProgressTracker:
    """440: persistent progress events per venture."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "venture_progress.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, venture_id, status, **details):
        row = {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "venture_id":venture_id,
            "status":status,
            "details":details,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
