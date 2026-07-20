from __future__ import annotations
import json, os, time
from pathlib import Path

class RunLock:
    """277: prevent overlapping autonomous improvement cycles."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "improvement_cycle.lock"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def acquire(self, stale_after_seconds=7200):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                created = float(data.get("created", 0))
                if time.time() - created < stale_after_seconds:
                    return {"acquired": False, "reason": "cycle_already_running", "lock": data}
            except Exception:
                pass
            self.path.unlink(missing_ok=True)

        data = {"pid": os.getpid(), "created": time.time()}
        self.path.write_text(json.dumps(data), encoding="utf-8")
        return {"acquired": True, "lock": data}

    def release(self):
        self.path.unlink(missing_ok=True)
        return {"released": True}
