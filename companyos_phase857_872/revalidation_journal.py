import json
from pathlib import Path
from datetime import datetime,timezone
class RevalidationJournal:
    def __init__(self,root):
        self.path=Path(root)/".companyos_runtime"/"revalidation_journal.jsonl"
        self.path.parent.mkdir(parents=True,exist_ok=True)
    def append(self,row):
        x={"timestamp":datetime.now(timezone.utc).isoformat(),**row}
        with self.path.open("a",encoding="utf-8") as f:f.write(json.dumps(x,default=str)+"\n")
        return x
