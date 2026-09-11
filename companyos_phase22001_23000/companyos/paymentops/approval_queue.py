import json
from pathlib import Path
from datetime import datetime, timezone

class PaymentApprovalQueue:
    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "payment_approval_queue.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def enqueue(self, payload):
        row = dict(payload)
        row.setdefault("status","pending")
        row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row

    def pending(self):
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("status") == "pending":
                out.append(row)
        return out
