#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
LOGS="$ROOT/logs"
BACKUP="$ROOT/backups/phase18_step8_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$LOGS" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 8 - Autonomous Orchestrator"
echo "============================================================"

for file in \
  "$AGENTS/autonomous_orchestrator.py" \
  "$CTL/orchestratorctl" \
  "$MEMORY/autonomous_orchestrator_config.json" \
  "$MEMORY/autonomous_orchestrator_state.json" \
  "$MEMORY/autonomous_orchestrator_health.json" \
  "$MEMORY/autonomous_orchestrator_audit.json" \
  "$MEMORY/autonomous_operations_config.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/autonomous_orchestrator_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_cycle_execution": true,
  "continue_on_noncritical_failure": true,
  "maximum_retries_per_step": 1,
  "step_timeout_seconds": 300,
  "automatic_internal_analysis": true,
  "automatic_internal_planning": true,
  "automatic_internal_reporting": true,
  "automatic_local_backup": true,
  "automatic_integrity_check": true,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false,
  "pipeline": [
    {
      "id": "integrity",
      "critical": true,
      "command": ["python", "companyos/integrityctl", "check"]
    },
    {
      "id": "opportunity-discovery",
      "critical": false,
      "command": ["python", "companyos/opportunitydiscoveryctl", "discover"]
    },
    {
      "id": "priority-ranking",
      "critical": true,
      "command": ["python", "companyos/priorityctl", "rank"]
    },
    {
      "id": "decision-preparation",
      "critical": false,
      "command": ["python", "companyos/decisionctl", "prepare"]
    },
    {
      "id": "execution-planning",
      "critical": false,
      "command": ["python", "companyos/executionplanctl", "prepare"]
    },
    {
      "id": "continuous-improvement",
      "critical": false,
      "command": ["python", "companyos/improvementctl", "analyze"]
    },
    {
      "id": "performance-analytics",
      "critical": false,
      "command": ["python", "companyos/performancectl", "collect"]
    },
    {
      "id": "business-forecast",
      "critical": false,
      "command": ["python", "companyos/forecastctl", "forecast"]
    },
    {
      "id": "executive-brief",
      "critical": false,
      "command": ["python", "companyos/briefctl", "generate"]
    }
  ]
}
JSON

cat > "$AGENTS/autonomous_orchestrator.py" <<'PY'
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

CONFIG = MEMORY / "autonomous_orchestrator_config.json"
STATE = MEMORY / "autonomous_orchestrator_state.json"
HEALTH = MEMORY / "autonomous_orchestrator_health.json"
AUDIT = MEMORY / "autonomous_orchestrator_audit.json"
HALT = MEMORY / "HALT_AUTONOMY"
LOG_FILE = LOGS / "autonomous_orchestrator.log"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def run_command(command: list[str], timeout: int) -> dict[str, Any]:
    started = time.time()
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
            "stdout": proc.stdout[-5000:],
            "stderr": proc.stderr[-3000:],
            "duration_seconds": round(time.time() - started, 3),
        }
    except Exception as exc:
        return {
            "success": False,
            "return_code": 1,
            "error": str(exc),
            "duration_seconds": round(time.time() - started, 3),
        }


def run_cycle() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "autonomous_orchestrator_disabled",
        }
        audit("cycle", result)
        return result

    if HALT.exists():
        result = {
            "success": False,
            "status": "autonomy_halted",
            "halt_file": str(HALT),
        }
        audit("cycle", result)
        return result

    pipeline = config.get("pipeline", [])
    timeout = max(30, int(config.get("step_timeout_seconds", 300)))
    retries = max(0, int(config.get("maximum_retries_per_step", 1)))

    cycle_results = []
    critical_failure = False

    for step in pipeline:
        step_id = str(step.get("id"))
        command = [str(x) for x in step.get("command", [])]
        critical = bool(step.get("critical", False))

        if not command:
            result = {
                "id": step_id,
                "success": False,
                "critical": critical,
                "error": "Empty command",
            }
            cycle_results.append(result)
            if critical:
                critical_failure = True
                break
            continue

        log(f"Starting orchestrator step: {step_id}")

        attempt_results = []
        final = None

        for attempt in range(retries + 1):
            current = run_command(command, timeout)
            current["attempt"] = attempt + 1
            attempt_results.append(current)
            final = current

            if current.get("success"):
                break

        step_result = {
            "id": step_id,
            "critical": critical,
            "success": bool(final and final.get("success")),
            "attempts": attempt_results,
        }
        cycle_results.append(step_result)

        log(
            f"Finished orchestrator step: {step_id} "
            f"success={step_result['success']}"
        )

        if not step_result["success"] and critical:
            critical_failure = True
            break

        if (
            not step_result["success"]
            and not config.get("continue_on_noncritical_failure", True)
        ):
            break

    success = not critical_failure

    state = load_json(
        STATE,
        {
            "schema_version": 1,
            "cycle_count": 0,
        },
    )
    state["cycle_count"] = int(state.get("cycle_count", 0)) + 1
    state["last_cycle_at"] = now()
    state["last_cycle_success"] = success
    state["last_cycle_results"] = cycle_results
    save_json(STATE, state)

    failures = [
        item for item in cycle_results
        if not item.get("success", False)
    ]

    save_json(
        HEALTH,
        {
            "healthy": success,
            "last_cycle_at": now(),
            "cycle_count": state["cycle_count"],
            "step_count": len(cycle_results),
            "failure_count": len(failures),
            "critical_failure": critical_failure,
            "last_error": (
                failures[0].get("error")
                if failures else None
            ),
        },
    )

    result = {
        "success": success,
        "status": "autonomous_orchestrator_cycle_complete",
        "cycle_count": state["cycle_count"],
        "steps_run": len(cycle_results),
        "failures": len(failures),
        "critical_failure": critical_failure,
        "results": cycle_results,
    }
    audit("cycle", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "autonomous_orchestrator_status",
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

    if action == "run":
        return print_result(run_cycle())

    if action == "status":
        return print_result(status())

    return print_result({
        "success": False,
        "status": "unknown_orchestrator_action",
        "action": action,
        "allowed": ["run", "status"],
    })


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/autonomous_orchestrator.py"

cat > "$CTL/orchestratorctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "autonomous_orchestrator.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/orchestratorctl"

echo "[1/6] Compiling..."
python -m py_compile \
  "$AGENTS/autonomous_orchestrator.py" \
  "$CTL/orchestratorctl"

echo "[2/6] Running autonomous orchestration cycle..."
python "$CTL/orchestratorctl" run

echo "[3/6] Adding orchestrator to scheduler..."
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
    "id": "autonomous-orchestrator",
    "enabled": True,
    "interval_seconds": 3600,
    "command": ["python", "companyos/orchestratorctl", "run"]
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

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking orchestrator..."
python "$CTL/orchestratorctl" status
python "$CTL/operationsctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "autonomous_orchestrator.py",
    root / "companyos" / "orchestratorctl",
    root / "ceo_memory" / "autonomous_orchestrator_config.json",
    root / "ceo_memory" / "autonomous_orchestrator_state.json",
    root / "ceo_memory" / "autonomous_orchestrator_health.json",
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
        "automatic_customer_contact",
        "automatic_publication",
        "automatic_spending",
        "automatic_destructive_actions",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

    state = json.loads(required[3].read_text(encoding="utf-8"))
    if int(state.get("cycle_count", 0)) < 1:
        errors.append("No orchestrator cycle completed")

    scheduler = json.loads(required[5].read_text(encoding="utf-8"))
    job = next(
        (
            item for item in scheduler.get("jobs", [])
            if item.get("id") == "autonomous-orchestrator"
        ),
        None,
    )

    if not job:
        errors.append("Autonomous orchestrator scheduler job missing")
    elif job.get("enabled") is not True:
        errors.append("Autonomous orchestrator scheduler job disabled")

except Exception as exc:
    errors.append(f"Verification data error: {exc}")

print("--------------------------------------------")
print("Phase 18 Step 8 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 STEP 8 INSTALLED"
echo " AUTONOMOUS ORCHESTRATOR ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/orchestratorctl run"
echo "  python companyos/orchestratorctl status"
echo
echo "Autonomous schedule:"
echo "  Full orchestration cycle runs every hour"
echo
echo "Pipeline:"
echo "  Integrity -> Opportunities -> Priorities -> Decisions"
echo "  -> Execution Plans -> Improvement -> Performance"
echo "  -> Forecast -> Executive Brief"
echo
echo "Emergency halt:"
echo "  python companyos/autonomyctl halt"
