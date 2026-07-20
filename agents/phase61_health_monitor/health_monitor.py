import json
from datetime import datetime, timezone
from pathlib import Path

from agents.phase58_persistent_runtime.runtime_manager import status as runtime_status
from agents.phase60_watchdog_supervisor.watchdog_supervisor import status as supervisor_status

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase61"
STATE_FILE = MEMORY / "health_state.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def health_check():
    runtime = runtime_status()
    supervisor = supervisor_status()

    process_alive = bool(runtime.get("process_alive"))
    runtime_state = runtime.get("state", {})
    failure_count = runtime_state.get("consecutive_failures", 0) or 0

    healthy = process_alive and failure_count < 3

    result = {
        "success": True,
        "status": "phase61_health_ok" if healthy else "phase61_health_degraded",
        "healthy": healthy,
        "checked_at": now(),
        "runtime_process_alive": process_alive,
        "runtime_status": runtime_state.get("status"),
        "consecutive_failures": failure_count,
        "watchdog_supervisor_status": supervisor.get("state", {}).get("status"),
    }
    return save(result)

if __name__ == "__main__":
    print(json.dumps(health_check(), indent=2))
