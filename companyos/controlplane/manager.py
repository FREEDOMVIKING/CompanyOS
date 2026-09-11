from datetime import datetime, timezone
import time
from .config import log_dir, runtime_dir, services
from .health import collect_health
from .processes import pid_alive, start_module, stop_pid
from .storage import atomic_write_json, read_json

class ControlPlane:
    def __init__(self):
        self.runtime = runtime_dir()
        self.logs = log_dir()
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime / "services.json"

    def _state(self):
        return read_json(self.state_path, {"services": {}, "updated_at": None})

    def _write(self, state):
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        atomic_write_json(self.state_path, state)

    def start(self):
        state = self._state()
        state.setdefault("services", {})
        for spec in services():
            existing = state["services"].get(spec.name, {})
            old_pid = int(existing.get("pid", 0) or 0)
            if not spec.enabled:
                state["services"][spec.name] = {
                    "enabled": False, "module": spec.module, "status": "unavailable", "pid": 0
                }
                continue
            if old_pid and pid_alive(old_pid):
                state["services"][spec.name] = {**existing, "enabled": True, "status": "running"}
                continue
            pid = start_module(spec.module, self.logs / f"{spec.name}.log")
            state["services"][spec.name] = {
                "enabled": True,
                "module": spec.module,
                "status": "running",
                "pid": pid,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "restart_count": int(existing.get("restart_count", 0)),
            }
        self._write(state)
        time.sleep(0.5)
        health = collect_health()
        atomic_write_json(self.runtime / "system_health.json", health)
        return health

    def stop(self):
        state = self._state()
        for item in state.get("services", {}).values():
            pid = int(item.get("pid", 0) or 0)
            stopped = stop_pid(pid) if pid else True
            item["status"] = "stopped" if stopped else "stop_failed"
            item["pid"] = 0 if stopped else pid
        self._write(state)
        health = collect_health()
        atomic_write_json(self.runtime / "system_health.json", health)
        return health

    def restart(self):
        self.stop()
        return self.start()

    def status(self):
        health = collect_health()
        atomic_write_json(self.runtime / "system_health.json", health)
        return health
