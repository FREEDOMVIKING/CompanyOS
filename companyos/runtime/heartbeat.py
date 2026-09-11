import json
from pathlib import Path
from datetime import datetime, timezone

class RuntimeHeartbeat:
    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"runtime_heartbeat.json"
        self.path.parent.mkdir(parents=True,exist_ok=True)

    def beat(self, service, state=None):
        row={
            "service":service,
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "state":state or {}
        }
        self.path.write_text(json.dumps(row,indent=2,default=str),encoding="utf-8")
        return row

    def read(self):
        if not self.path.exists(): return {}
        try: return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception: return {}
