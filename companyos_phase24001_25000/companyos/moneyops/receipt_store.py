import json
from pathlib import Path
from datetime import datetime, timezone

class ReceiptStore:
    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "multichain_receipts.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, payload):
        row = dict(payload)
        row.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row

    def recent(self, limit=100):
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines()[-int(limit):]:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
        return out
