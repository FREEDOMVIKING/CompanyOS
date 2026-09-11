import json, hashlib
from pathlib import Path
from datetime import datetime, timezone

class ExecutionReceiptStore:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"execution_receipts.jsonl"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def record(self, job, capability, result):
        body={"job_id":job.get("job_id"),"capability":capability,"result":result}
        digest=hashlib.sha256(json.dumps(body,sort_keys=True,default=str).encode()).hexdigest()
        row={
            "timestamp":datetime.now(timezone.utc).isoformat(),
            **body,
            "digest":digest
        }
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,default=str)+"\n")
        return row
