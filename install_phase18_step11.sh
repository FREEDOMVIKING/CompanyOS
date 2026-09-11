#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
LOGS="$ROOT/logs"
BACKUP="$ROOT/backups/phase18_step11_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$LOGS" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 11 - Autonomous Exception & Recovery Engine"
echo "============================================================"

for file in \
  "$AGENTS/exception_recovery_engine.py" \
  "$CTL/recoveryctl" \
  "$MEMORY/exception_recovery_config.json" \
  "$MEMORY/exception_recovery_state.json" \
  "$MEMORY/exception_recovery_health.json" \
  "$MEMORY/exception_recovery_audit.json" \
  "$MEMORY/autonomous_operations_config.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/exception_recovery_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_exception_detection": true,
  "automatic_retry": true,
  "automatic_scheduler_recovery": true,
  "automatic_integrity_recheck": true,
  "automatic_backup_before_recovery": true,
  "max_retries_per_issue": 2,
  "retry_backoff_seconds": 5,
  "maximum_recoveries_per_hour": 5,
  "automatic_code_changes": false,
  "automatic_destructive_actions": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false
}
JSON

cat > "$AGENTS/exception_recovery_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
LOGS = ROOT / "logs"

CONFIG = MEMORY / "exception_recovery_config.json"
STATE = MEMORY / "exception_recovery_state.json"
HEALTH = MEMORY / "exception_recovery_health.json"
AUDIT = MEMORY / "exception_recovery_audit.json"
HALT = MEMORY / "HALT_AUTONOMY"

OPS_STATE = MEMORY / "autonomous_operations_state.json"
OPS_HEALTH = MEMORY / "autonomous_operations_health.json"
WATCHDOG_HEALTH = MEMORY / "watchdog_health.json"
ORCH_HEALTH = MEMORY / "autonomous_orchestrator_health.json"
INTEGRITY_HEALTH = MEMORY / "system_integrity_health.json"

LOG_FILE = LOGS / "exception_recovery.log"


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
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    tmp.replace(path)


def log(message: str) -> None:
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


def run(command: list[str], timeout: int = 300) -> dict[str, Any]:
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


def detect_issues() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    ops_health = load_json(OPS_HEALTH, {})
    watchdog_health = load_json(WATCHDOG_HEALTH, {})
    orch_health = load_json(ORCH_HEALTH, {})
    integrity_health = load_json(INTEGRITY_HEALTH, {})
    ops_state = load_json(OPS_STATE, {})

    if ops_health and ops_health.get("healthy") is False:
        issues.append({
            "id": "autonomous-operations-unhealthy",
            "severity": "high",
            "recovery": "restart-scheduler",
        })

    if watchdog_health and watchdog_health.get("healthy") is False:
        issues.append({
            "id": "watchdog-unhealthy",
            "severity": "high",
            "recovery": "restart-watchdog",
        })

    if orch_health and orch_health.get("healthy") is False:
        issues.append({
            "id": "orchestrator-unhealthy",
            "severity": "medium",
            "recovery": "run-orchestrator",
        })

    if integrity_health and integrity_health.get("healthy") is False:
        issues.append({
            "id": "integrity-unhealthy",
            "severity": "critical",
            "recovery": "integrity-check",
        })

    for job_id, job_state in ops_state.get("jobs", {}).items():
        failures = int(job_state.get("failure_count", 0))
        last_success = job_state.get("last_success")

        if last_success is False and failures > 0:
            issues.append({
                "id": f"job-failure:{job_id}",
                "severity": "medium",
                "recovery": "run-scheduler-cycle",
                "job_id": job_id,
            })

    deduped = {}
    for issue in issues:
        deduped[issue["id"]] = issue

    return list(deduped.values())


def recovery_allowed(state: dict[str, Any], config: dict[str, Any]) -> bool:
    history = [
        float(item)
        for item in state.get("recovery_epochs", [])
        if epoch() - float(item) < 3600
    ]
    state["recovery_epochs"] = history
    maximum = int(config.get("maximum_recoveries_per_hour", 5))
    return len(history) < maximum


def execute_recovery(issue: dict[str, Any]) -> dict[str, Any]:
    recovery = issue.get("recovery")

    if recovery == "restart-scheduler":
        return run([sys.executable, "companyos/operationsctl", "restart"], 120)

    if recovery == "restart-watchdog":
        return run([sys.executable, "companyos/watchdogctl", "restart"], 120)

    if recovery == "run-orchestrator":
        return run([sys.executable, "companyos/orchestratorctl", "run"], 300)

    if recovery == "integrity-check":
        return run([sys.executable, "companyos/integrityctl", "check"], 300)

    if recovery == "run-scheduler-cycle":
        return run([sys.executable, "companyos/operationsctl", "run-once"], 300)

    return {
        "success": False,
        "error": f"Unknown recovery action: {recovery}",
    }


def recover() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {"success": False, "status": "exception_recovery_disabled"}
        audit("recover", result)
        return result

    if HALT.exists():
        result = {
            "success": False,
            "status": "autonomy_halted_no_recovery",
            "halt_file": str(HALT),
        }
        audit("recover", result)
        return result

    issues = detect_issues()

    state = load_json(
        STATE,
        {
            "schema_version": 1,
            "recovery_epochs": [],
            "issue_history": [],
            "recovery_count": 0,
        },
    )

    if not recovery_allowed(state, config):
        result = {
            "success": False,
            "status": "recovery_rate_limit_reached",
            "issues": issues,
        }
        audit("recover", result)
        return result

    if not issues:
        save_json(
            HEALTH,
            {
                "healthy": True,
                "last_checked_at": now(),
                "issue_count": 0,
                "recovery_attempted": False,
                "last_error": None,
            },
        )
        result = {
            "success": True,
            "status": "no_recovery_needed",
            "issues": [],
        }
        audit("recover", result)
        return result

    actions = []

    if config.get("automatic_backup_before_recovery", True):
        backup = run([sys.executable, "companyos/integrityctl", "backup"], 300)
        actions.append({
            "type": "backup",
            "success": backup.get("success", False),
            "result": backup,
        })

    max_retries = max(0, int(config.get("max_retries_per_issue", 2)))
    backoff = max(0, int(config.get("retry_backoff_seconds", 5)))

    unresolved = []

    for issue in issues:
        attempts = []
        resolved = False

        for attempt in range(max_retries + 1):
            result = execute_recovery(issue)
            attempts.append({
                "attempt": attempt + 1,
                "result": result,
            })

            if result.get("success"):
                resolved = True
                break

            if attempt < max_retries and backoff:
                time.sleep(backoff * (attempt + 1))

        actions.append({
            "type": "issue-recovery",
            "issue": issue,
            "resolved": resolved,
            "attempts": attempts,
        })

        if not resolved:
            unresolved.append(issue)

    if config.get("automatic_integrity_recheck", True):
        integrity = run([sys.executable, "companyos/integrityctl", "check"], 300)
        actions.append({
            "type": "post-recovery-integrity-check",
            "success": integrity.get("success", False),
            "result": integrity,
        })

    recovery_epoch = epoch()
    state.setdefault("recovery_epochs", []).append(recovery_epoch)
    state["recovery_count"] = int(state.get("recovery_count", 0)) + 1
    state["last_recovery_at"] = now()
    state["last_issue_count"] = len(issues)
    state["last_unresolved_count"] = len(unresolved)
    state.setdefault("issue_history", []).append({
        "timestamp": now(),
        "issues": issues,
        "unresolved": unresolved,
    })
    state["issue_history"] = state["issue_history"][-200:]
    save_json(STATE, state)

    healthy = len(unresolved) == 0

    save_json(
        HEALTH,
        {
            "healthy": healthy,
            "last_checked_at": now(),
            "issue_count": len(issues),
            "unresolved_count": len(unresolved),
            "recovery_attempted": True,
            "last_error": (
                None if healthy
                else f"{len(unresolved)} issue(s) unresolved"
            ),
        },
    )

    result = {
        "success": healthy,
        "status": (
            "exception_recovery_complete"
            if healthy else "exception_recovery_incomplete"
        ),
        "issues": issues,
        "unresolved": unresolved,
        "actions": actions,
    }
    audit("recover", result)
    return result


def check() -> dict[str, Any]:
    issues = detect_issues()
    result = {
        "success": True,
        "status": "exception_scan_complete",
        "issue_count": len(issues),
        "issues": issues,
    }
    audit("check", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "exception_recovery_status",
        "config": load_json(CONFIG, {}),
        "state": load_json(STATE, {}),
        "health": load_json(HEALTH, {}),
        "halted": HALT.exists(),
        "log": str(LOG_FILE),
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "check":
            return print_result(check())

        if action == "recover":
            return print_result(recover())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_recovery_action",
            "action": action,
            "allowed": ["check", "recover", "status"],
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "exception_recovery_error",
            "error": str(exc),
        }
        save_json(
            HEALTH,
            {
                "healthy": False,
                "last_checked_at": now(),
                "last_error": str(exc),
            },
        )
        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/exception_recovery_engine.py"

cat > "$CTL/recoveryctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "exception_recovery_engine.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/recoveryctl"

echo "[1/6] Compiling..."
python -m py_compile \
  "$AGENTS/exception_recovery_engine.py" \
  "$CTL/recoveryctl"

echo "[2/6] Scanning for exceptions..."
python "$CTL/recoveryctl" check

echo "[3/6] Running recovery pass..."
python "$CTL/recoveryctl" recover

echo "[4/6] Adding recovery job to autonomous scheduler..."
python - <<'PY'
import json
from pathlib import Path

root = Path.home() / "companyos"
path = root / "ceo_memory" / "autonomous_operations_config.json"

if not path.exists():
    raise SystemExit("autonomous_operations_config.json not found")

data = json.loads(path.read_text(encoding="utf-8"))
jobs = data.setdefault("jobs", [])

job = {
    "id": "exception-recovery",
    "enabled": True,
    "interval_seconds": 900,
    "command": ["python", "companyos/recoveryctl", "recover"]
}

existing = next(
    (item for item in jobs if item.get("id") == job["id"]),
    None,
)

if existing:
    existing.clear()
    existing.update(job)
else:
    jobs.append(job)

path.write_text(json.dumps(data, indent=2), encoding="utf-8")

print(json.dumps({
    "success": True,
    "job_id": job["id"],
    "interval_seconds": job["interval_seconds"]
}, indent=2))
PY

echo "[5/6] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/recoveryctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "exception_recovery_engine.py",
    root / "companyos" / "recoveryctl",
    root / "ceo_memory" / "exception_recovery_config.json",
    root / "ceo_memory" / "exception_recovery_state.json",
    root / "ceo_memory" / "exception_recovery_health.json",
    root / "ceo_memory" / "autonomous_operations_config.json",
]

for path in required:
    if not path.exists():
        errors.append(f"Missing: {path}")
    elif path.stat().st_size <= 0:
        errors.append(f"Empty: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"Compile error: {exc}")

try:
    config = json.loads(required[2].read_text(encoding="utf-8"))

    for field in [
        "automatic_code_changes",
        "automatic_destructive_actions",
        "automatic_customer_contact",
        "automatic_publication",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

    health = json.loads(required[4].read_text(encoding="utf-8"))
    if "healthy" not in health:
        errors.append("Recovery health missing healthy field")

    scheduler = json.loads(required[5].read_text(encoding="utf-8"))
    job = next(
        (
            item for item in scheduler.get("jobs", [])
            if item.get("id") == "exception-recovery"
        ),
        None,
    )

    if not job:
        errors.append("Exception recovery scheduler job missing")
    elif job.get("enabled") is not True:
        errors.append("Exception recovery scheduler job disabled")

except Exception as exc:
    errors.append(f"Verification data error: {exc}")

print("--------------------------------------------")
print("Phase 18 Step 11 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 STEP 11 INSTALLED"
echo " AUTONOMOUS EXCEPTION & RECOVERY ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/recoveryctl check"
echo "  python companyos/recoveryctl recover"
echo "  python companyos/recoveryctl status"
echo
echo "Autonomous schedule:"
echo "  Exception recovery runs every 15 minutes"
