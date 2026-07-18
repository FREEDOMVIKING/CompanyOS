#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
LOGS = ROOT / "logs"
RUN = ROOT / "run"

CONFIG = MEMORY / "watchdog_config.json"
STATE = MEMORY / "watchdog_state.json"
HEALTH = MEMORY / "watchdog_health.json"
AUDIT = MEMORY / "watchdog_audit.json"
HALT = MEMORY / "HALT_AUTONOMY"

PID_FILE = RUN / "companyos_watchdog.pid"
SCHEDULER_PID = RUN / "autonomous_operations.pid"
LOG_FILE = LOGS / "companyos_watchdog.log"

STOP_REQUESTED = False


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def epoch() -> float:
    return time.time()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)


def append_log(message: str) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[{now()}] {message}\n")


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT, [])
    if not isinstance(records, list):
        records = []

    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })

    save_json(AUDIT, records[-1000:])


def pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_pid(path: Path) -> int | None:
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
        return pid if pid_running(pid) else None
    except Exception:
        return None


def handle_stop(signum: int, frame: object) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True
    append_log(f"Stop requested by signal {signum}")


def run_command(command: list[str], timeout: int = 300) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-2000:],
        }
    except Exception as exc:
        return {
            "success": False,
            "return_code": 1,
            "error": str(exc),
        }


def restart_allowed(state: dict[str, Any], config: dict[str, Any]) -> bool:
    history = [
        float(item)
        for item in state.get("restart_epochs", [])
        if epoch() - float(item) < 3600
    ]
    state["restart_epochs"] = history

    maximum = int(config.get("maximum_restarts_per_hour", 3))
    if len(history) >= maximum:
        return False

    last_restart = float(state.get("last_restart_epoch", 0))
    cooldown = int(config.get("restart_cooldown_seconds", 300))
    return epoch() - last_restart >= cooldown


def recover_scheduler() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    state = load_json(
        STATE,
        {
            "schema_version": 1,
            "restart_epochs": [],
            "restart_count": 0,
        },
    )

    if HALT.exists():
        result = {
            "success": False,
            "status": "autonomy_halted_no_recovery",
        }
        audit("recover", result)
        return result

    if not restart_allowed(state, config):
        result = {
            "success": False,
            "status": "restart_limit_or_cooldown_active",
            "restart_epochs": state.get("restart_epochs", []),
        }
        audit("recover", result)
        return result

    actions = []

    if config.get("automatic_local_backup_before_recovery", True):
        backup = run_command(
            [sys.executable, "companyos/integrityctl", "backup"],
            timeout=300,
        )
        actions.append({"action": "backup", **backup})

    start = run_command(
        [sys.executable, "companyos/operationsctl", "start"],
        timeout=60,
    )
    actions.append({"action": "scheduler_start", **start})

    if (
        start.get("success")
        and config.get("automatic_integrity_check_after_restart", True)
    ):
        integrity = run_command(
            [sys.executable, "companyos/integrityctl", "check"],
            timeout=300,
        )
        actions.append({"action": "integrity_check", **integrity})

    success = bool(start.get("success"))

    if success:
        restart_time = epoch()
        state.setdefault("restart_epochs", []).append(restart_time)
        state["last_restart_epoch"] = restart_time
        state["last_restart_at"] = now()
        state["restart_count"] = int(state.get("restart_count", 0)) + 1

    save_json(STATE, state)

    result = {
        "success": success,
        "status": (
            "scheduler_recovered"
            if success else "scheduler_recovery_failed"
        ),
        "actions": actions,
        "restart_count": state.get("restart_count", 0),
    }
    audit("recover", result)
    return result


def check_once() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "watchdog_disabled",
        }
        audit("check", result)
        return result

    scheduler_pid = read_pid(SCHEDULER_PID)
    halted = HALT.exists()
    recovery = None

    if (
        not halted
        and scheduler_pid is None
        and config.get("automatic_scheduler_restart", True)
    ):
        append_log("Scheduler is not running; starting recovery")
        recovery = recover_scheduler()
        scheduler_pid = read_pid(SCHEDULER_PID)

    healthy = halted or scheduler_pid is not None

    health = {
        "healthy": healthy,
        "watchdog_running": read_pid(PID_FILE) is not None,
        "scheduler_running": scheduler_pid is not None,
        "scheduler_pid": scheduler_pid,
        "halted": halted,
        "last_checked_at": now(),
        "recovery_attempted": recovery is not None,
        "recovery_success": (
            recovery.get("success") if recovery else None
        ),
        "last_error": (
            None if healthy
            else (
                recovery.get("status")
                if recovery else "scheduler_not_running"
            )
        ),
    }
    save_json(HEALTH, health)

    result = {
        "success": healthy,
        "status": (
            "watchdog_check_passed"
            if healthy else "watchdog_check_failed"
        ),
        "health": health,
        "recovery": recovery,
    }
    audit("check", result)
    return result


def daemon() -> int:
    existing = read_pid(PID_FILE)
    if existing and existing != os.getpid():
        print(json.dumps({
            "success": False,
            "status": "watchdog_already_running",
            "pid": existing,
        }, indent=2))
        return 1

    RUN.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    append_log(f"Watchdog started with PID {os.getpid()}")

    try:
        while not STOP_REQUESTED:
            result = check_once()
            append_log(
                f"Check complete: success={result.get('success')} "
                f"scheduler={result.get('health', {}).get('scheduler_running')}"
            )

            config = load_json(CONFIG, {})
            interval = max(
                30,
                int(config.get("check_interval_seconds", 120)),
            )

            for _ in range(interval):
                if STOP_REQUESTED:
                    break
                time.sleep(1)
    finally:
        PID_FILE.unlink(missing_ok=True)
        append_log("Watchdog stopped")

    return 0


def start() -> dict[str, Any]:
    pid = read_pid(PID_FILE)

    if pid:
        result = {
            "success": True,
            "status": "watchdog_already_running",
            "pid": pid,
        }
        audit("start", result)
        return result

    LOGS.mkdir(parents=True, exist_ok=True)
    log_handle = LOG_FILE.open("a", encoding="utf-8")

    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__)), "daemon"],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=log_handle,
        start_new_session=True,
    )
    log_handle.close()

    for _ in range(30):
        time.sleep(0.1)
        pid = read_pid(PID_FILE)
        if pid:
            result = {
                "success": True,
                "status": "watchdog_started",
                "pid": pid,
                "log": str(LOG_FILE),
            }
            audit("start", result)
            return result

    result = {
        "success": False,
        "status": "watchdog_start_failed",
        "spawned_pid": proc.pid,
    }
    audit("start", result)
    return result


def stop() -> dict[str, Any]:
    pid = read_pid(PID_FILE)

    if not pid:
        result = {
            "success": True,
            "status": "watchdog_not_running",
        }
        audit("stop", result)
        return result

    os.kill(pid, signal.SIGTERM)

    for _ in range(50):
        time.sleep(0.1)
        if not pid_running(pid):
            PID_FILE.unlink(missing_ok=True)
            result = {
                "success": True,
                "status": "watchdog_stopped",
                "pid": pid,
            }
            audit("stop", result)
            return result

    result = {
        "success": False,
        "status": "watchdog_stop_timeout",
        "pid": pid,
    }
    audit("stop", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    state = load_json(STATE, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "companyos_watchdog_status",
        "enabled": config.get("enabled", False),
        "watchdog_running": read_pid(PID_FILE) is not None,
        "watchdog_pid": read_pid(PID_FILE),
        "scheduler_running": read_pid(SCHEDULER_PID) is not None,
        "scheduler_pid": read_pid(SCHEDULER_PID),
        "halted": HALT.exists(),
        "state": state,
        "health": health,
        "log": str(LOG_FILE),
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "check":
        return print_result(check_once())

    if action == "recover":
        return print_result(recover_scheduler())

    if action == "start":
        return print_result(start())

    if action == "stop":
        return print_result(stop())

    if action == "restart":
        stop()
        return print_result(start())

    if action == "status":
        return print_result(status())

    if action == "daemon":
        return daemon()

    return print_result({
        "success": False,
        "status": "unknown_watchdog_action",
        "action": action,
        "allowed": [
            "check",
            "recover",
            "start",
            "stop",
            "restart",
            "status",
        ],
    })


if __name__ == "__main__":
    raise SystemExit(main())
