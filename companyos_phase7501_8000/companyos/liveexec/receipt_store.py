import json
from pathlib import Path
from datetime import datetime, timezone

class LiveExecutionReceiptStore:
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"liveexec_receipts.jsonl"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def append(self,record):
        row={"timestamp":datetime.now(timezone.utc).isoformat(),**record}
        with self.path.open("a",encoding="utf-8") as f:f.write(json.dumps(row,default=str)+"\n")
        return row
