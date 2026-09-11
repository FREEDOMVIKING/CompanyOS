#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
LOGS="$ROOT/logs"
RUN="$ROOT/run"
BACKUP="$ROOT/backups/phase18_step4_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$LOGS" "$RUN" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 4 - Autonomous Operations Scheduler"
echo "============================================================"

for file in \
  "$AGENTS/autonomous_operations_scheduler.py" \
  "$CTL/operationsctl" \
  "$MEMORY/autonomous_operations_config.json" \
  "$MEMORY/autonomous_operations_state.json" \
  "$MEMORY/autonomous_operations_health.json" \
  "$MEMORY/autonomous_operations_audit.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/autonomous_operations_config.json" <<'JSON'
{
  "enabled": true,
  "loop_interval_seconds": 900,
  "maximum_jobs_per_cycle": 20,
  "stop_cycle_on_job_failure": false,
  "require_autonomy_not_halted": true,
  "automatic_local_execution": true,
  "automatic_internal_analysis": true,
  "automatic_internal_reporting": true,
  "automatic_backups": true,
  "automatic_integrity_checks": true,
  "automatic_git_stage": false,
  "automatic_git_commit": false,
  "automatic_git_push": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "jobs": [
    {
      "id": "integrity-check",
      "enabled": true,
      "interval_seconds": 3600,
      "command": ["python", "companyos/integrityctl", "check"]
    },
    {
      "id": "opportunity-discovery",
      "enabled": true,
      "interval_seconds": 1800,
      "command": ["python", "companyos/opportunitydiscoveryctl", "discover"]
    },
    {
      "id": "priority-ranking",
      "enabled": true,
      "interval_seconds": 1800,
      "command": ["python", "companyos/priorityctl", "rank"]
    },
    {
      "id": "decision-preparation",
      "enabled": true,
      "interval_seconds": 1800,
      "command": ["python", "companyos/decisionctl", "prepare"]
    },
    {
      "id": "execution-plan-preparation",
      "enabled": true,
      "interval_seconds": 1800,
      "command": ["python", "companyos/executionplanctl", "prepare"]
    },
    {
      "id": "improvement-analysis",
      "enabled": true,
      "interval_seconds": 3600,
      "command": ["python", "companyos/improvementctl", "analyze"]
    },
    {
      "id": "performance-analytics",
      "enabled": true,
      "interval_seconds": 3600,
      "command": ["python", "companyos/performancectl", "collect"]
    },
    {
      "id": "business-forecast",
      "enabled": true,
      "interval_seconds": 7200,
      "command": ["python", "companyos/forecastctl", "forecast"]
    },
    {
      "id": "local-backup",
      "enabled": true,
      "interval_seconds": 21600,
      "command": ["python", "companyos/integrityctl", "backup"]
    }
  ]
}
JSON

cat > "$AGENTS/autonomous_operations_scheduler.py" <<'PY'
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


def run_job(job: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job["id"])
    command = [str(part) for part in job.get("command", [])]
    started_epoch = epoch()
    started_at = now()

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
        }
    else:
        try:
            proc = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=max(60, int(job.get("timeout_seconds", 300))),
            )
            result = {
                "id": job_id,
                "success": proc.returncode == 0,
                "return_code": proc.returncode,
                "stdout": proc.stdout[-5000:],
                "stderr": proc.stderr[-3000:],
                "started_at": started_at,
                "finished_at": now(),
                "duration_seconds": round(epoch() - started_epoch, 3),
            }
        except Exception as exc:
            result = {
                "id": job_id,
                "success": False,
                "return_code": 1,
                "error": str(exc),
                "started_at": started_at,
                "finished_at": now(),
                "duration_seconds": round(epoch() - started_epoch, 3),
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
PY

chmod +x "$AGENTS/autonomous_operations_scheduler.py"

cat > "$CTL/operationsctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "autonomous_operations_scheduler.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/operationsctl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/autonomous_operations_scheduler.py" \
  "$CTL/operationsctl"

echo "[2/5] Running one full autonomous cycle..."
python "$CTL/operationsctl" run-all

echo "[3/5] Starting background scheduler..."
python "$CTL/operationsctl" start

echo "[4/5] Checking scheduler status..."
python "$CTL/operationsctl" status

echo "[5/5] Verifying..."
python - <<'PY'
import json
import os
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "autonomous_operations_scheduler.py",
    root / "companyos" / "operationsctl",
    root / "ceo_memory" / "autonomous_operations_config.json",
    root / "ceo_memory" / "autonomous_operations_state.json",
    root / "ceo_memory" / "autonomous_operations_health.json",
    root / "run" / "autonomous_operations.pid",
]

for path in required:
    if not path.exists():
        errors.append(f"Missing: {path}")
    elif path.is_file() and path.stat().st_size <= 0:
        errors.append(f"Empty: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"Compile error: {exc}")

try:
    config = json.loads(required[2].read_text(encoding="utf-8"))

    for field in [
        "automatic_customer_contact",
        "automatic_publication",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

    pid = int(required[5].read_text(encoding="utf-8").strip())
    os.kill(pid, 0)

    state = json.loads(required[3].read_text(encoding="utf-8"))
    if int(state.get("cycle_count", 0)) < 1:
        errors.append("No autonomous cycle completed")

except Exception as exc:
    errors.append(f"Runtime verification failed: {exc}")

print("--------------------------------------------")
print("Phase 18 Step 4 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 STEP 4 INSTALLED"
echo " AUTONOMOUS SCHEDULER RUNNING"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/operationsctl status"
echo "  python companyos/operationsctl run-once"
echo "  python companyos/operationsctl run-all"
echo "  python companyos/operationsctl start"
echo "  python companyos/operationsctl stop"
echo "  python companyos/operationsctl restart"
echo
echo "Emergency halt:"
echo "  python companyos/autonomyctl halt"
echo
echo "Log:"
echo "  tail -f logs/autonomous_operations.log"
