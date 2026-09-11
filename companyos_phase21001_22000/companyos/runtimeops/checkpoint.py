import json
from pathlib import Path
from datetime import datetime, timezone

class RuntimeCheckpoint:
    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "autonomy_checkpoint.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, payload):
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(row, indent=2, default=str), encoding="utf-8")
        tmp.replace(self.path)
        return row

    def load(self):
        if not self.path.exists():
            return None
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return None
