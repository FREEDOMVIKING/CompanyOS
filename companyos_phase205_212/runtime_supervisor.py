from pathlib import Path
import json, time

class RuntimeSupervisor:
    """211: persistent queue/state/heartbeat primitives for the self-building runtime."""

    def __init__(self, project_root):
        self.root = Path(project_root)
        self.state_dir = self.root / ".companyos_runtime"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.state_dir / "selfbuild_queue.json"
        self.heartbeat_file = self.state_dir / "heartbeat.json"

    def _read_queue(self):
        if not self.queue_file.exists():
            return []
        try:
            return json.loads(self.queue_file.read_text())
        except Exception:
            return []

    def enqueue(self, job):
        q = self._read_queue()
        q.append(job)
        self.queue_file.write_text(json.dumps(q, indent=2))
        return {"queued": True, "queue_depth": len(q)}

    def next_job(self):
        q = self._read_queue()
        if not q:
            return None
        job = q.pop(0)
        self.queue_file.write_text(json.dumps(q, indent=2))
        return job

    def heartbeat(self, status="healthy"):
        data = {"status": status, "timestamp": time.time()}
        self.heartbeat_file.write_text(json.dumps(data, indent=2))
        return data
