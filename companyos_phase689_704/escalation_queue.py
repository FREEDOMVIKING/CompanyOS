import json
from pathlib import Path
from datetime import datetime, timezone

class EscalationQueue:
    """701: durable human escalation queue."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "executive_escalation_queue.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return []
        try:
            data=json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data,list) else []
        except Exception:
            return []

    def add(self, item):
        items=self.load()
        item={"created_at":datetime.now(timezone.utc).isoformat(),**item}
        items.append(item)
        self.path.write_text(json.dumps(items,indent=2,default=str),encoding="utf-8")
        return item
