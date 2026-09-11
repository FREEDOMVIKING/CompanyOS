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

CONFIG = MEMORY / "autonomous_operations_config.json"
STATE = MEMORY / "autonomous_operations_state.json"
HEALTH = MEMORY / "autonomous_operations_health.json"
AUDIT = MEMORY / "autonomous_operations_audit.json"
HALT = MEMORY / "HALT_AUTONOMY"
PID_FILE = RUN / "autonomous_operations.pid"
LOG_FILE = LOGS / "autonomous_operations.log"
LOCK_FILE = RUN / "autonomous_operations.lock"

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


def handle_stop(signum: int, frame: object) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True
    append_log(f"Stop requested by signal {signum}")


def pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def current_pid() -> int | None:
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        return pid if pid_running(pid) else None
    except Exception:
        return None


def load_state() -> dict[str, Any]:
    state = load_json(
        STATE,
        {
            "schema_version": 1,
            "cycle_count": 0,
            "jobs": {},
            "last_cycle_at": None,
        },
    )
    state.setdefault("jobs", {})
    return state


def due(job: dict[str, Any], state: dict[str, Any], force: bool) -> bool:
    if force:
        return True

    last_run = (
        state.get("jobs", {})
        .get(job["id"], {})
        .get("last_started_epoch")
    )

    if last_run is None:
        return True

    interval = max(60, int(job.get("interval_seconds", 900)))
    return epoch() - float(last_run) >= interval



def _mem_available_mb():
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except Exception:
        pass
    return 999999


def _companyos_process_count():
    count = 0
    try:
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                cmd = (
                    (entry / "cmdline")
                    .read_bytes()
                    .replace(b"\\0", b" ")
                    .decode(errors="ignore")
                    .lower()
                )
            except Exception:
                continue

            if "companyos" in cmd and "python" in cmd:
                count += 1
    except Exception:
        pass

    return count


def phone_resource_gate():
    min_available_mb = 2500
    max_companyos_processes = 18

    available = _mem_available_mb()
    processes = _companyos_process_count()

    return {
        "ok": (
            available >= min_available_mb
            and processes <= max_companyos_processes
        ),
        "available_mb": available,
        "companyos_processes": processes,
    }



def _scheduled_command_pid(command):
    """
    Return the PID of an already-running copy of this scheduled
    command, or None if no copy exists.
    """
    target = " ".join(str(x) for x in command).strip()

    if not target:
        return None

    my_pid = os.getpid()

    try:
        proc_root = Path("/proc")

        for entry in proc_root.iterdir():
            if not entry.name.isdigit():
                continue

            pid = int(entry.name)

            if pid == my_pid:
                continue

            try:
                cmdline = (
                    (entry / "cmdline")
                    .read_bytes()
                    .replace(b"\0", b" ")
                    .decode(errors="ignore")
                    .strip()
                )
            except Exception:
                continue

            if target in cmdline:
                return pid

    except Exception:
        pass

    return None


def _kill_job_process_group(proc, grace_seconds=5):
    """
    Stop the whole subprocess tree created for one scheduled job.
    """
    if proc is None:
        return

    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass

    try:
        proc.wait(timeout=grace_seconds)
        return
    except Exception:
        pass

    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

    try:
        proc.wait(timeout=2)
    except Exception:
        pass


def run_job(job: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job["id"])
    command = [str(part) for part in job.get("command", [])]
    started_epoch = epoch()
    started_at = now()

    resources = phone_resource_gate()

    if not resources["ok"]:
        result = {
            "id": job_id,
            "success": False,
            "return_code": None,
            "error": "resource_pressure",
            "started_at": started_at,
            "finished_at": now(),
            "duration_seconds": 0,
            "available_mb": resources["available_mb"],
            "companyos_processes": resources["companyos_processes"],
        }

        append_log(
            f"Deferred job {job_id}: resource pressure "
            f"available_mb={resources['available_mb']} "
            f"companyos_processes={resources['companyos_processes']}"
        )

        return result

    state["jobs"].setdefault(job_id, {})
    state["jobs"][job_id].update({
        "last_started_at": started_at,
        "last_started_epoch": started_epoch,
        "last_command": command,
        "status": "running",
    })
    save_json(STATE, state)

    append_log(f"Starting job {job_id}: {' '.join(command)}")

    if not command:
        result = {
            "id": job_id,
            "success": False,
            "return_code": 1,
            "error": "Empty command",
            "started_at": started_at,
            "finished_at": now(),
            "duration_seconds": round(epoch() - started_epoch, 3),
        }

    else:
        existing_pid = _scheduled_command_pid(command)

        if existing_pid:
            result = {
                "id": job_id,
                "success": True,
                "return_code": None,
                "status": "already_running",
                "existing_pid": existing_pid,
                "started_at": started_at,
                "finished_at": now(),
                "duration_seconds": round(
                    epoch() - started_epoch, 3
                ),
            }

            append_log(
                f"Skipped duplicate job {job_id}: "
                f"existing_pid={existing_pid}"
            )

        else:
            proc = None

            try:
                timeout_seconds = max(
                    60,
                    int(job.get("timeout_seconds", 300))
                )

                proc = subprocess.Popen(
                    command,
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                )

                try:
                    stdout, stderr = proc.communicate(
                        timeout=timeout_seconds
                    )

                    result = {
                        "id": job_id,
                        "success": proc.returncode == 0,
                        "return_code": proc.returncode,
                        "stdout": (stdout or "")[-5000:],
                        "stderr": (stderr or "")[-3000:],
                        "started_at": started_at,
                        "finished_at": now(),
                        "duration_seconds": round(
                            epoch() - started_epoch, 3
                        ),
                    }

                except subprocess.TimeoutExpired:
                    append_log(
                        f"Job timeout {job_id}: "
                        f"pid={proc.pid} "
                        f"timeout={timeout_seconds}s"
                    )

                    _kill_job_process_group(proc)

                    try:
                        stdout, stderr = proc.communicate(
                            timeout=2
                        )
                    except Exception:
                        stdout, stderr = "", ""

                    result = {
                        "id": job_id,
                        "success": False,
                        "return_code": proc.returncode,
                        "status": "timeout",
                        "error": "job_timeout",
                        "stdout": (stdout or "")[-5000:],
                        "stderr": (stderr or "")[-3000:],
                        "started_at": started_at,
                        "finished_at": now(),
                        "duration_seconds": round(
                            epoch() - started_epoch, 3
                        ),
                    }

            except Exception as exc:
                if proc is not None:
                    _kill_job_process_group(proc)

                result = {
                    "id": job_id,
                    "success": False,
                    "return_code": 1,
                    "error": str(exc),
                    "started_at": started_at,
                    "finished_at": now(),
                    "duration_seconds": round(
                        epoch() - started_epoch, 3
                    ),
                }

    job_state = state["jobs"][job_id]
    job_state.update({
        "last_finished_at": result.get("finished_at", now()),
        "last_success": result["success"],
        "last_return_code": result.get("return_code"),
        "last_duration_seconds": result.get("duration_seconds"),
        "status": "success" if result["success"] else "failed",
        "run_count": int(job_state.get("run_count", 0)) + 1,
        "failure_count": int(job_state.get("failure_count", 0))
        + (0 if result["success"] else 1),
    })

    save_json(STATE, state)
    append_log(
        f"Finished job {job_id}: "
        f"{'success' if result['success'] else 'failed'}"
    )
    return result


def cycle(force: bool = False) -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "autonomous_operations_disabled",
        }
        audit("cycle", result)
        return result

    if config.get("require_autonomy_not_halted", True) and HALT.exists():
        result = {
            "success": False,
            "status": "autonomy_halted",
            "halt_file": str(HALT),
        }
        audit("cycle", result)
        return result

    state = load_state()
    jobs = [
        item for item in config.get("jobs", [])
        if item.get("enabled", True)
    ]

    maximum = max(1, int(config.get("maximum_jobs_per_cycle", 20)))
    selected = [
        job for job in jobs
        if due(job, state, force)
    ][:maximum]

    results = []

    for job in selected:
        if STOP_REQUESTED:
            break

        result = run_job(job, state)
        results.append(result)

        if (
            not result["success"]
            and config.get("stop_cycle_on_job_failure", False)
        ):
            break

    state["cycle_count"] = int(state.get("cycle_count", 0)) + 1
    state["last_cycle_at"] = now()
    state["last_cycle_job_count"] = len(results)
    state["last_cycle_success"] = all(
        item.get("success", False) for item in results
    )
    save_json(STATE, state)

    failures = [
        item for item in results
        if not item.get("success", False)
    ]

    health = {
        "healthy": not failures,
        "running": current_pid() is not None,
        "halted": HALT.exists(),
        "last_cycle_at": state["last_cycle_at"],
        "last_cycle_job_count": len(results),
        "failure_count": len(failures),
        "last_error": (
            failures[0].get("error")
            or failures[0].get("stderr")
            if failures else None
        ),
    }
    save_json(HEALTH, health)

    result = {
        "success": not failures,
        "status": "autonomous_operations_cycle_complete",
        "force": force,
        "jobs_due": len(selected),
        "jobs_run": len(results),
        "failures": len(failures),
        "results": results,
    }
    audit("cycle", result)
    return result


def daemon() -> int:
    existing = current_pid()
    if existing and existing != os.getpid():
        print(json.dumps({
            "success": False,
            "status": "scheduler_already_running",
            "pid": existing,
        }, indent=2))
        return 1

    RUN.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    LOCK_FILE.write_text(now(), encoding="utf-8")

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    append_log(f"Scheduler daemon started with PID {os.getpid()}")

    try:
        while not STOP_REQUESTED:
            result = cycle(force=False)
            append_log(
                f"Cycle complete: success={result.get('success')} "
                f"jobs={result.get('jobs_run', 0)}"
            )

            config = load_json(CONFIG, {})
            interval = max(
                60,
                int(config.get("loop_interval_seconds", 900)),
            )

            for _ in range(interval):
                if STOP_REQUESTED:
                    break
                time.sleep(1)
    finally:
        PID_FILE.unlink(missing_ok=True)
        LOCK_FILE.unlink(missing_ok=True)
        append_log("Scheduler daemon stopped")

    return 0


def start() -> dict[str, Any]:
    pid = current_pid()
    if pid:
        return {
            "success": True,
            "status": "scheduler_already_running",
            "pid": pid,
        }

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

    for _ in range(20):
        time.sleep(0.1)
        pid = current_pid()
        if pid:
            result = {
                "success": True,
                "status": "scheduler_started",
                "pid": pid,
                "log": str(LOG_FILE),
            }
            audit("start", result)
            return result

    result = {
        "success": False,
        "status": "scheduler_start_failed",
        "spawned_pid": proc.pid,
    }
    audit("start", result)
    return result


def stop() -> dict[str, Any]:
    pid = current_pid()

    if not pid:
        result = {
            "success": True,
            "status": "scheduler_not_running",
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
                "status": "scheduler_stopped",
                "pid": pid,
            }
            audit("stop", result)
            return result

    result = {
        "success": False,
        "status": "scheduler_stop_timeout",
        "pid": pid,
    }
    audit("stop", result)
    return result


def status() -> dict[str, Any]:
    pid = current_pid()
    config = load_json(CONFIG, {})
    state = load_state()
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "autonomous_operations_status",
        "enabled": config.get("enabled", False),
        "running": pid is not None,
        "pid": pid,
        "halted": HALT.exists(),
        "loop_interval_seconds": config.get("loop_interval_seconds"),
        "configured_job_count": len(config.get("jobs", [])),
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

    if action == "run-once":
        return print_result(cycle(force=False))

    if action == "run-all":
        return print_result(cycle(force=True))

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
        "status": "unknown_operations_action",
        "action": action,
        "allowed": [
            "run-once",
            "run-all",
            "start",
            "stop",
            "restart",
            "status",
        ],
    })


if __name__ == "__main__":
    raise SystemExit(main())
