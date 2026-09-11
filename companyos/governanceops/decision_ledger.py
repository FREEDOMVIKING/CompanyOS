import json, hashlib
from pathlib import Path
from datetime import datetime, timezone

class DecisionLedger:
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"decision_ledger.jsonl"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def append(self,decision):
        payload=json.dumps(decision,sort_keys=True,default=str)
        row={
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "decision":decision,
            "digest":hashlib.sha256(payload.encode()).hexdigest()
        }
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,default=str)+"\n")
        return row
