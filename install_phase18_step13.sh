#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase18_step13_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 13 - Autonomous Internal Action Engine"
echo "============================================================"

for file in \
  "$AGENTS/internal_action_engine.py" \
  "$CTL/actionctl" \
  "$MEMORY/internal_action_config.json" \
  "$MEMORY/internal_action_queue.json" \
  "$MEMORY/internal_action_state.json" \
  "$MEMORY/internal_action_health.json" \
  "$MEMORY/internal_action_audit.json" \
  "$MEMORY/autonomous_operations_config.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/internal_action_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_action_generation": true,
  "automatic_internal_execution": true,
  "maximum_actions_per_cycle": 10,
  "allowed_actions": [
    "priority-rank",
    "decision-prepare",
    "execution-plan-prepare",
    "improvement-analyze",
    "performance-collect",
    "forecast-run",
    "brief-generate",
    "goal-generate",
    "learning-run",
    "integrity-check",
    "backup-create"
  ],
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false,
  "credential_access": false,
  "private_key_access": false
}
JSON

cat > "$AGENTS/internal_action_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "internal_action_config.json"
QUEUE = MEMORY / "internal_action_queue.json"
STATE = MEMORY / "internal_action_state.json"
HEALTH = MEMORY / "internal_action_health.json"
AUDIT = MEMORY / "internal_action_audit.json"
HALT = MEMORY / "HALT_AUTONOMY"

GOALS = MEMORY / "goal_strategy_goals.json"
DECISIONS = MEMORY / "ceo_decision_queue.json"
PRIORITIES = MEMORY / "executive_priority_rankings.json"

ACTION_MAP = {
    "priority-rank": ["python", "companyos/priorityctl", "rank"],
    "decision-prepare": ["python", "companyos/decisionctl", "prepare"],
    "execution-plan-prepare": ["python", "companyos/executionplanctl", "prepare"],
    "improvement-analyze": ["python", "companyos/improvementctl", "analyze"],
    "performance-collect": ["python", "companyos/performancectl", "collect"],
    "forecast-run": ["python", "companyos/forecastctl", "forecast"],
    "brief-generate": ["python", "companyos/briefctl", "generate"],
    "goal-generate": ["python", "companyos/goalctl", "generate"],
    "learning-run": ["python", "companyos/learningctl", "learn"],
    "integrity-check": ["python", "companyos/integrityctl", "check"],
    "backup-create": ["python", "companyos/integrityctl", "backup"],
}


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


def add_action(queue: list[dict[str, Any]], action: str, reason: str, priority: int) -> None:
    if any(
        item.get("action") == action and item.get("status") == "pending"
        for item in queue
    ):
        return

    queue.append({
        "id": f"{action}-{int(datetime.now().timestamp())}",
        "action": action,
        "reason": reason,
        "priority": priority,
        "status": "pending",
        "created_at": now(),
        "external_action": False,
    })


def generate_queue() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    store = load_json(
        QUEUE,
        {"schema_version": 1, "actions": []},
    )
    queue = store.setdefault("actions", [])

    priorities = load_json(PRIORITIES, {}).get("rankings", {}).get("priorities", [])
    decisions = load_json(DECISIONS, {}).get("decisions", [])
    goals = load_json(GOALS, {}).get("goals", [])

    critical = sum(1 for item in priorities if item.get("priority_band") == "critical")
    pending_decisions = sum(1 for item in decisions if item.get("status") == "pending")
    active_goals = sum(1 for item in goals if item.get("status") == "active")

    add_action(queue, "integrity-check", "Maintain system integrity before autonomous work.", 100)

    if critical:
        add_action(queue, "priority-rank", f"{critical} critical priorities detected.", 95)

    if pending_decisions:
        add_action(queue, "decision-prepare", f"{pending_decisions} decisions pending.", 90)
        add_action(queue, "execution-plan-prepare", "Keep approved decisions translated into internal plans.", 85)

    if active_goals:
        add_action(queue, "performance-collect", f"{active_goals} active goals require measurement.", 80)
        add_action(queue, "forecast-run", "Refresh forecast against current goals.", 75)

    add_action(queue, "improvement-analyze", "Continuously search for internal process improvements.", 70)
    add_action(queue, "learning-run", "Update internal learning feedback.", 65)
    add_action(queue, "goal-generate", "Refresh autonomous goals and strategy.", 60)
    add_action(queue, "brief-generate", "Refresh executive summary.", 55)

    queue.sort(key=lambda x: int(x.get("priority", 0)), reverse=True)

    save_json(
        QUEUE,
        {
            "schema_version": 1,
            "generated_at": now(),
            "actions": queue,
        },
    )

    result = {
        "success": True,
        "status": "internal_action_queue_generated",
        "pending_count": sum(1 for x in queue if x.get("status") == "pending"),
    }
    audit("generate", result)
    return result


def run_action(action_name: str) -> dict[str, Any]:
    config = load_json(CONFIG, {})
    allowed = set(config.get("allowed_actions", []))

    if action_name not in allowed or action_name not in ACTION_MAP:
        return {
            "success": False,
            "status": "action_not_allowed",
            "action": action_name,
        }

    try:
        proc = subprocess.run(
            ACTION_MAP[action_name],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=300,
        )
        return {
            "success": proc.returncode == 0,
            "status": "action_executed",
            "action": action_name,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-2000:],
        }
    except Exception as exc:
        return {
            "success": False,
            "status": "action_execution_error",
            "action": action_name,
            "error": str(exc),
        }


def execute() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {"success": False, "status": "internal_action_engine_disabled"}
        audit("execute", result)
        return result

    if HALT.exists():
        result = {"success": False, "status": "autonomy_halted"}
        audit("execute", result)
        return result

    generate_queue()

    store = load_json(QUEUE, {"actions": []})
    actions = store.get("actions", [])
    maximum = max(1, int(config.get("maximum_actions_per_cycle", 10)))

    selected = [x for x in actions if x.get("status") == "pending"][:maximum]
    results = []

    for item in selected:
        result = run_action(str(item.get("action")))
        item["status"] = "completed" if result.get("success") else "failed"
        item["finished_at"] = now()
        item["result"] = result
        results.append(result)

    save_json(QUEUE, store)

    failures = [x for x in results if not x.get("success")]

    state = {
        "generated_at": now(),
        "actions_run": len(results),
        "failures": len(failures),
        "results": results,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False,
    }
    save_json(STATE, state)

    save_json(
        HEALTH,
        {
            "healthy": len(failures) == 0,
            "last_execution_at": now(),
            "actions_run": len(results),
            "failure_count": len(failures),
            "last_error": failures[0].get("status") if failures else None,
        },
    )

    result = {
        "success": len(failures) == 0,
        "status": "internal_action_cycle_complete",
        "actions_run": len(results),
        "failures": len(failures),
        "results": results,
    }
    audit("execute", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "internal_action_status",
        "config": load_json(CONFIG, {}),
        "state": load_json(STATE, {}),
        "health": load_json(HEALTH, {}),
    }
    audit("status", result)
    return result


def show_queue() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "internal_action_queue",
        "queue": load_json(QUEUE, {}),
    }
    audit("queue", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "generate":
            return print_result(generate_queue())
        if action == "execute":
            return print_result(execute())
        if action == "queue":
            return print_result(show_queue())
        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_action_engine_action",
            "action": action,
            "allowed": ["generate", "execute", "queue", "status"],
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "internal_action_engine_error",
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

chmod +x "$AGENTS/internal_action_engine.py"

cat > "$CTL/actionctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "internal_action_engine.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/actionctl"

echo "[1/6] Compiling..."
python -m py_compile \
  "$AGENTS/internal_action_engine.py" \
  "$CTL/actionctl"

echo "[2/6] Generating autonomous internal action queue..."
python "$CTL/actionctl" generate

echo "[3/6] Executing internal action cycle..."
python "$CTL/actionctl" execute

echo "[4/6] Adding internal action engine to scheduler..."
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
    "id": "internal-action-engine",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/actionctl", "execute"]
}

existing = next((x for x in jobs if x.get("id") == job["id"]), None)

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
python "$CTL/actionctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "internal_action_engine.py",
    root / "companyos" / "actionctl",
    root / "ceo_memory" / "internal_action_config.json",
    root / "ceo_memory" / "internal_action_queue.json",
    root / "ceo_memory" / "internal_action_state.json",
    root / "ceo_memory" / "internal_action_health.json",
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
        "credential_access",
        "private_key_access",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

    state = json.loads(required[4].read_text(encoding="utf-8"))
    if "actions_run" not in state:
        errors.append("Internal action state missing actions_run")

    scheduler = json.loads(required[6].read_text(encoding="utf-8"))
    job = next(
        (x for x in scheduler.get("jobs", []) if x.get("id") == "internal-action-engine"),
        None,
    )

    if not job:
        errors.append("Internal action scheduler job missing")
    elif job.get("enabled") is not True:
        errors.append("Internal action scheduler job disabled")

except Exception as exc:
    errors.append(f"Verification data error: {exc}")

print("--------------------------------------------")
print("Phase 18 Step 13 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 STEP 13 INSTALLED"
echo " AUTONOMOUS INTERNAL ACTION ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/actionctl generate"
echo "  python companyos/actionctl execute"
echo "  python companyos/actionctl queue"
echo "  python companyos/actionctl status"
echo
echo "Autonomous schedule:"
echo "  Internal action cycle runs every 30 minutes"
