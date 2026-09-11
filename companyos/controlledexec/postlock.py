import json
from pathlib import Path
from datetime import datetime, timezone

class PostExecutionLock:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"post_execution_lock.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def engage(self, reason="controlled_execution_complete"):
        data = {
            "locked": True,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"success":True,"status":"post_execution_lock_engaged","state":data}

    def clear(self):
        data = {
            "locked": False,
            "reason": "manual_clear",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"success":True,"status":"post_execution_lock_cleared","state":data}

    def status(self):
        if not self.path.exists():
            return {"locked":False,"reason":"no_lock_file"}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"locked":True,"reason":"lock_state_corrupt"}
