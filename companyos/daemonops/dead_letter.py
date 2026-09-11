import json
from pathlib import Path
class DeadLetterQueue:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"dead_letter.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
    def add(self, job, reason):
        rows=[]
        if self.path.exists():
            try: rows=json.loads(self.path.read_text(encoding="utf-8"))
            except Exception: rows=[]
        row={"job":job,"reason":reason}
        rows.append(row)
        self.path.write_text(json.dumps(rows,indent=2,default=str),encoding="utf-8")
        return row
