import json, hashlib
from pathlib import Path
from datetime import datetime, timezone

class ReleaseLedger:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"release_ledger.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, release):
        body = json.dumps(release, sort_keys=True, default=str)
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "release": release,
            "digest": hashlib.sha256(body.encode()).hexdigest()
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
