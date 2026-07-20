from __future__ import annotations
import json
from pathlib import Path

class FailureTracker:
    """279: track repeated failure loops and stop hammering the same broken path."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "improvement_failures.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if not self.path.exists():
            return {"consecutive_failures": 0, "last_reason": None}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"consecutive_failures": 0, "last_reason": None}
        except Exception:
            return {"consecutive_failures": 0, "last_reason": None}

    def record(self, success, reason=None):
        data = self._load()
        if success:
            data["consecutive_failures"] = 0
            data["last_reason"] = None
        else:
            data["consecutive_failures"] = int(data.get("consecutive_failures", 0)) + 1
            data["last_reason"] = reason
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    def state(self):
        return self._load()
