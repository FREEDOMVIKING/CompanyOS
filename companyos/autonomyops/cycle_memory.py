import json
from pathlib import Path
from datetime import datetime, timezone

class CycleMemory:
    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "autonomy_cycle_memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, payload):
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row

    def recent(self, limit=50):
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines()[-int(limit):]:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
        return rows
