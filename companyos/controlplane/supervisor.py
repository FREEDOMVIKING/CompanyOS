import signal
import time
from datetime import datetime, timezone
from .config import log_dir, runtime_dir, services
from .processes import pid_alive, start_module
from .storage import atomic_write_json, read_json

RUNNING = True

def stop(_sig, _frame):
    global RUNNING
    RUNNING = False

def supervise():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    state_path = runtime_dir() / "services.json"
    while RUNNING:
        state = read_json(state_path, {"services": {}})
        changed = False
        for spec in services():
            if spec.name == "supervisor_18301_18400" or not spec.enabled:
                continue
            item = state.get("services", {}).get(spec.name, {})
            pid = int(item.get("pid", 0) or 0)
            if not pid_alive(pid):
                new_pid = start_module(spec.module, log_dir() / f"{spec.name}.log")
                state.setdefault("services", {})[spec.name] = {
                    **item,
                    "enabled": True,
                    "module": spec.module,
                    "status": "restarted",
                    "pid": new_pid,
                    "last_restart_at": datetime.now(timezone.utc).isoformat(),
                    "restart_count": int(item.get("restart_count", 0)) + 1,
                }
                changed = True
        if changed:
            state["updated_at"] = datetime.now(timezone.utc).isoformat()
            atomic_write_json(state_path, state)
        for _ in range(10):
            if not RUNNING:
                break
            time.sleep(1)

if __name__ == "__main__":
    supervise()
