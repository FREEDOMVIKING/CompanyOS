import json
from pathlib import Path

class GovernanceLedger:
    """703: append-only governance audit ledger."""

    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"governance_ledger.jsonl"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def append(self, record):
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(record,default=str)+"\n")
        return record
