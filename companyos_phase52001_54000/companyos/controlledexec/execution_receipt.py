import json
from pathlib import Path
from datetime import datetime, timezone

class ControlledExecutionReceipt:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"controlled_execution_receipts.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, row):
        data = dict(row or {})
        data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")
        return data

    def recent(self, limit=50):
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines()[-int(limit):]:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
        return out
