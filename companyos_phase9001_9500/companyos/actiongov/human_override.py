import json
from pathlib import Path
from datetime import datetime, timezone

class HumanOverrideRegistry:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"human_overrides.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def add(self, scope, rule, actor="human"):
        rows=[]
        if self.path.exists():
            try: rows=json.loads(self.path.read_text(encoding="utf-8"))
            except Exception: rows=[]
        row={"scope":scope,"rule":rule,"actor":actor,"timestamp":datetime.now(timezone.utc).isoformat()}
        rows.append(row)
        self.path.write_text(json.dumps(rows,indent=2),encoding="utf-8")
        return row
