import json
from pathlib import Path
from datetime import datetime, timezone

class ExecutiveMemory:
    def __init__(self, root=None):
        self.root = Path(root or Path.home()/".companyos"/"executive_memory")
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root/"events.jsonl"

    def remember(self, kind, payload):
        row = {"ts": datetime.now(timezone.utc).isoformat(), "kind": kind, "payload": payload}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row

    def recent(self, limit=50):
        if not self.path.exists(): return []
        rows = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(x) for x in rows[-limit:] if x.strip()]
