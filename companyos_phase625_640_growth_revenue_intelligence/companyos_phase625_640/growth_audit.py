import json
from datetime import datetime, timezone
from pathlib import Path

class GrowthAudit:
    """637: append-only growth/revenue intelligence audit."""

    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"growth_intelligence_audit.jsonl"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def append(self, venture_id, result):
        row={"timestamp":datetime.now(timezone.utc).isoformat(),"venture_id":venture_id,"result":result}
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,default=str)+"\n")
        return row
