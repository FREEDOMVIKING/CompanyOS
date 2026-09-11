import json
from pathlib import Path
from datetime import datetime, timezone

class ExecutionReceiptStore:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"connector_execution_receipts.jsonl"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def append(self, connector, action, result):
        row={
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "connector":connector,
            "action":action,
            "result":result
        }
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,default=str)+"\n")
        return row
