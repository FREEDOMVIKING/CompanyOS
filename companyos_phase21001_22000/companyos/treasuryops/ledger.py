import json
from pathlib import Path
from datetime import datetime, timezone, date

class TreasuryLedger:
    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "treasury_ledger.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, row):
        item = dict(row)
        item.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, default=str) + "\n")
        return item

    def rows(self):
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
        return out

    def today_total(self, kind="debit"):
        today = date.today().isoformat()
        total = 0.0
        for row in self.rows():
            if str(row.get("timestamp",""))[:10] != today:
                continue
            if row.get("direction") != kind:
                continue
            try:
                total += float(row.get("amount", 0) or 0)
            except Exception:
                pass
        return round(total, 8)
