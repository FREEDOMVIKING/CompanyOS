import json
from datetime import datetime, timezone
from pathlib import Path

class QualityMemory:
    """525: append-only memory of quality decisions."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "opportunity_quality_memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, candidate):
        row = {"timestamp":datetime.now(timezone.utc).isoformat(), **candidate}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
