from __future__ import annotations
import json, time
from pathlib import Path

class SelfBuildDaemon:
    """233: persistent self-build queue and heartbeat controller."""

    def __init__(self, project_root):
        self.root = Path(project_root)
        self.state = self.root / ".companyos_runtime"
        self.state.mkdir(parents=True, exist_ok=True)
        self.queue = self.state / "model_selfbuild_queue.json"
        self.heartbeat = self.state / "model_selfbuild_heartbeat.json"

    def _read(self):
        if not self.queue.exists():
            return []
        try:
            value = json.loads(self.queue.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except Exception:
            return []

    def enqueue(self, mission):
        q = self._read()
        q.append(mission)
        self.queue.write_text(json.dumps(q, indent=2), encoding="utf-8")
        return {"queued": True, "depth": len(q)}

    def pop(self):
        q = self._read()
        if not q:
            return None
        item = q.pop(0)
        self.queue.write_text(json.dumps(q, indent=2), encoding="utf-8")
        return item

    def beat(self, status="idle"):
        data = {"status": status, "timestamp": time.time()}
        self.heartbeat.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
