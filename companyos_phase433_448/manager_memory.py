import json
from datetime import datetime, timezone
from pathlib import Path

class ManagerMemory:
    """445: append-only execution-manager memory."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "venture_manager_memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event):
        row = {"timestamp":datetime.now(timezone.utc).isoformat(), **event}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
