import json
import os
import subprocess
import sys
from pathlib import Path

from agents.phase58_persistent_runtime.runtime_state import (
    load_state,
    save_state,
    request_stop,
)

ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "ceo_memory" / "phase58"
LOG_FILE = LOG_DIR / "persistent_worker.log"
PID_FILE = LOG_DIR / "persistent_worker.pid"

LOG_DIR.mkdir(parents=True, exist_ok=True)


def pid_alive(pid):
    if not pid:
        return False

    try:
        os.kill(int(pid), 0)
        return True
    except (ProcessLookupError, ValueError):
        return False
    except PermissionError:
        return True


def status():
    state = load_state()
    pid = state.get("pid")
    alive = pid_alive(pid)

    if state.get("status") == "running" and not alive:
        state["status"] = "stopped"
        state["pid"] = None
        save_state(state)

    return {
        "success": True,
        "status": "phase58_runtime_manager_status",
        "process_alive": alive,
        "state": state,
    }


def start():
    current = status()
    state = current["state"]

    if current.get("process_alive"):
        return {
            "success": False,
            "status": "phase58_already_running",
            "pid": state.get("pid"),
        }

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    with open(LOG_FILE, "a") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "from agents.phase58_persistent_runtime.persistent_worker "
                    "import run_worker; run_worker()"
                ),
            ],
            cwd=str(ROOT),
            env=env,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )

    PID_FILE.write_text(str(process.pid))

    return {
        "success": True,
        "status": "phase58_runtime_start_requested",
        "pid": process.pid,
        "log_file": str(LOG_FILE),
    }


def stop():
    state = request_stop()

    return {
        "success": True,
        "status": "phase58_runtime_stop_requested",
        "pid": state.get("pid"),
        "stop_requested": True,
    }


def main():
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "status"

    if command == "status":
        result = status()
    elif command == "start":
        result = start()
    elif command == "stop":
        result = stop()
    else:
        result = {
            "success": False,
            "status": "unknown_command",
            "available_commands": [
                "status",
                "start",
                "stop",
            ],
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
