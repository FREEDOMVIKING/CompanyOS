import json
from pathlib import Path
from datetime import datetime, timezone

class RevenueTracker:
    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "venture_revenue.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, venture_id, revenue=0, cost=0, note=""):
        row = {
            "venture_id": venture_id,
            "revenue": float(revenue),
            "cost": float(cost),
            "profit": float(revenue) - float(cost),
            "note": note,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        return row

    def summary(self, venture_id=None):
        rows = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                    if venture_id is None or r.get("venture_id") == venture_id:
                        rows.append(r)
                except Exception:
                    pass
        revenue = sum(float(r.get("revenue",0)) for r in rows)
        cost = sum(float(r.get("cost",0)) for r in rows)
        return {
            "revenue": round(revenue,8),
            "cost": round(cost,8),
            "profit": round(revenue-cost,8),
            "records": len(rows)
        }
