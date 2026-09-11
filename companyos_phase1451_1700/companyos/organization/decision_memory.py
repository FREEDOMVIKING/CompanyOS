import json
from pathlib import Path
from datetime import datetime, timezone

class DecisionMemory:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"executive_decision_memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, kind, payload):
        row = {"timestamp": datetime.now(timezone.utc).isoformat(), "kind": kind, "payload": payload}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row

    def recent(self, limit=100):
        if not self.path.exists():
            return []
        rows = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(x) for x in rows[-limit:] if x.strip()]
