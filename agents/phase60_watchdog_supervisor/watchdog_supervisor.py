import json
import time
from datetime import datetime, timezone
from pathlib import Path

from agents.phase59_runtime_watchdog.runtime_watchdog import watchdog_check

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase60"
STATE_FILE = MEMORY / "watchdog_supervisor_state.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load_state():
    if not STATE_FILE.exists():
        return {
            "phase": 60,
            "status": "ready",
            "checks": 0,
            "restart_events": 0,
            "last_check": None,
            "last_result_status": None,
            "stop_requested": False,
        }
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {
            "phase": 60,
            "status": "recovered",
            "checks": 0,
            "restart_events": 0,
            "last_check": None,
            "last_result_status": "state_recovered",
            "stop_requested": False,
        }

def save_state(state):
    state["updated_at"] = now()
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return state

def request_stop():
    state = load_state()
    state["stop_requested"] = True
    state["status"] = "stop_requested"
    return save_state(state)

def clear_stop():
    state = load_state()
    state["stop_requested"] = False
    state["status"] = "ready"
    return save_state(state)

def run_supervisor(interval_seconds=60, max_checks=None):
    state = load_state()
    state["status"] = "running"
    save_state(state)

    checks_this_run = 0

    while True:
        state = load_state()
        if state.get("stop_requested"):
            state["status"] = "stopped"
            save_state(state)
            return {
                "success": True,
                "status": "phase60_watchdog_supervisor_stopped",
                "checks_this_run": checks_this_run,
                "state": state,
            }

        if max_checks is not None and checks_this_run >= max_checks:
            state["status"] = "ready"
            save_state(state)
            return {
                "success": True,
                "status": "phase60_max_checks_reached",
                "checks_this_run": checks_this_run,
                "state": state,
            }

        result = watchdog_check(auto_restart=True)
        checks_this_run += 1

        state = load_state()
        state["checks"] = state.get("checks", 0) + 1
        state["last_check"] = now()
        state["last_result_status"] = result.get("status")
        if result.get("status") == "phase59_restart_requested":
            state["restart_events"] = state.get("restart_events", 0) + 1
        save_state(state)

        if max_checks is None or checks_this_run < max_checks:
            time.sleep(max(1, int(interval_seconds)))

def status():
    return {
        "success": True,
        "status": "phase60_watchdog_supervisor_status",
        "state": load_state(),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
