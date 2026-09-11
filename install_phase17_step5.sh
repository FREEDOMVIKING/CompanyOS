#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase17_step5_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$BACKUP"

echo "============================================================"
echo " Phase 17 Step 5 - Decision Execution Planner"
echo "============================================================"

for file in \
  "$AGENTS/decision_execution_planner.py" \
  "$CTL/executionplanctl" \
  "$MEMORY/decision_execution_config.json" \
  "$MEMORY/decision_execution_plans.json" \
  "$MEMORY/decision_execution_health.json" \
  "$MEMORY/decision_execution_audit.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/decision_execution_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_plan_generation": true,
  "automatic_internal_task_creation": true,
  "automatic_task_execution": false,
  "automatic_customer_contact": false,
  "automatic_external_execution": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "owner_approval_required_for_external_actions": true,
  "maximum_steps_per_plan": 8
}
JSON

[ -f "$MEMORY/decision_execution_plans.json" ] || cat > "$MEMORY/decision_execution_plans.json" <<'JSON'
{
  "schema_version": 1,
  "plans": [],
  "statistics": {
    "total": 0,
    "draft": 0,
    "ready": 0,
    "completed": 0,
    "blocked": 0
  },
  "last_updated_at": null
}
JSON

cat > "$AGENTS/decision_execution_planner.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "decision_execution_config.json"
DECISIONS = MEMORY / "ceo_decision_queue.json"
PLANS = MEMORY / "decision_execution_plans.json"
TASKS = MEMORY / "product_execution_tasks.json"
HEALTH = MEMORY / "decision_execution_health.json"
AUDIT = MEMORY / "decision_execution_audit.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def make_id(prefix: str, seed: str) -> str:
    digest = hashlib.sha256(
        f"{seed}:{now()}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{prefix}-{digest}"


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


def update_stats(store: dict[str, Any]) -> None:
    plans = store.get("plans", [])
    statuses = ["draft", "ready", "completed", "blocked"]

    stats = {"total": len(plans)}
    for status in statuses:
        stats[status] = sum(
            1 for item in plans
            if item.get("status") == status
        )

    store["statistics"] = stats
    store["last_updated_at"] = now()


def plan_steps(decision: dict[str, Any]) -> list[dict[str, Any]]:
    category = str(decision.get("category") or "general")
    title = str(decision.get("title") or "Decision")

    templates: dict[str, list[tuple[str, str]]] = {
        "finance": [
            ("Verify financial record", "Confirm the amount and supporting records."),
            ("Assess collection options", "Prepare internal collection options for owner review."),
            ("Prepare owner recommendation", "Summarize the safest next step."),
            ("Record outcome", "Update the internal decision and finance records.")
        ],
        "sales": [
            ("Review customer context", "Review the CRM history and current opportunity."),
            ("Define next sales step", "Prepare the next internal sales action."),
            ("Prepare communication draft", "Create a draft without sending it."),
            ("Record owner decision", "Wait for owner approval before external contact.")
        ],
        "operations": [
            ("Review current state", "Inspect project, task, and milestone records."),
            ("Identify blocker", "Document the main blocker or dependency."),
            ("Create internal work steps", "Break the work into safe internal tasks."),
            ("Validate completion", "Confirm results before marking complete.")
        ],
    }

    selected = templates.get(
        category,
        [
            ("Review decision", f"Review the context for {title}."),
            ("Prepare options", "Create safe internal options."),
            ("Choose internal next step", "Select the best internal action."),
            ("Record outcome", "Update CompanyOS memory.")
        ],
    )

    return [
        {
            "order": index,
            "name": name,
            "description": description,
            "status": "pending",
            "internal_execution_allowed": True,
            "external_execution_allowed": False,
            "completed_at": None,
        }
        for index, (name, description) in enumerate(selected, start=1)
    ]


def prepare_plans() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "decision_execution_planner_disabled",
        }
        audit("prepare", result)
        return result

    decisions = [
        item
        for item in load_json(DECISIONS, {}).get("decisions", [])
        if item.get("status") == "approved"
    ]

    store = load_json(
        PLANS,
        {
            "schema_version": 1,
            "plans": [],
            "statistics": {},
        },
    )

    existing = {
        str(item.get("decision_id"))
        for item in store.get("plans", [])
    }

    created = []

    for decision in decisions:
        decision_id = str(decision.get("id"))

        if decision_id in existing:
            continue

        steps = plan_steps(decision)[: int(config.get("maximum_steps_per_plan", 8))]

        plan = {
            "id": make_id("plan", decision_id),
            "decision_id": decision_id,
            "title": decision.get("title"),
            "category": decision.get("category"),
            "status": "ready",
            "steps": steps,
            "progress_percent": 0,
            "automatic_task_execution": False,
            "automatic_customer_contact": False,
            "automatic_external_execution": False,
            "automatic_publication": False,
            "automatic_spending": False,
            "created_at": now(),
            "updated_at": now(),
        }

        store.setdefault("plans", []).append(plan)
        created.append(plan)

    update_stats(store)
    save_json(PLANS, store)

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_prepared_at": now(),
            "created_count": len(created),
            "ready_count": store.get("statistics", {}).get("ready", 0),
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "decision_execution_plans_prepared",
        "created_count": len(created),
        "plans": created,
        "automatic_task_execution": False,
        "automatic_external_execution": False,
    }

    audit("prepare", result)
    return result


def create_tasks(plan_id: str) -> dict[str, Any]:
    plans_store = load_json(PLANS, {})
    plan = next(
        (
            item for item in plans_store.get("plans", [])
            if item.get("id") == plan_id
        ),
        None,
    )

    if not plan:
        result = {
            "success": False,
            "status": "execution_plan_not_found",
            "plan_id": plan_id,
        }
        audit("create_tasks", result)
        return result

    task_store = load_json(
        TASKS,
        {
            "schema_version": 1,
            "tasks": [],
            "statistics": {},
        },
    )
    tasks = task_store.setdefault("tasks", [])
    existing = {
        (str(item.get("source_id")), str(item.get("name")))
        for item in tasks
    }

    created = []

    for step in plan.get("steps", []):
        key = (plan_id, str(step.get("name")))

        if key in existing:
            continue

        task = {
            "id": make_id("task", f"{plan_id}:{step.get('name')}"),
            "name": step.get("name"),
            "description": step.get("description"),
            "source_id": plan_id,
            "type": "decision_execution",
            "status": "pending",
            "internal_execution_allowed": True,
            "external_execution_allowed": False,
            "automatic_execution": False,
            "created_at": now(),
            "updated_at": now(),
        }

        tasks.append(task)
        created.append(task)
        existing.add(key)

    save_json(TASKS, task_store)

    result = {
        "success": True,
        "status": "decision_execution_tasks_created",
        "plan_id": plan_id,
        "created_count": len(created),
        "tasks": created,
        "automatic_execution": False,
        "external_execution_allowed": False,
    }

    audit("create_tasks", result)
    return result


def list_plans() -> dict[str, Any]:
    store = load_json(PLANS, {})
    result = {
        "success": True,
        "status": "decision_execution_plan_list",
        "statistics": store.get("statistics", {}),
        "plans": store.get("plans", []),
    }
    audit("list", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    store = load_json(PLANS, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "decision_execution_planner_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_plan_generation": config.get(
            "automatic_internal_plan_generation", False
        ),
        "automatic_internal_task_creation": config.get(
            "automatic_internal_task_creation", False
        ),
        "automatic_task_execution": config.get(
            "automatic_task_execution", False
        ),
        "automatic_customer_contact": config.get(
            "automatic_customer_contact", False
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_publication": config.get(
            "automatic_publication", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "statistics": store.get("statistics", {}),
        "health": health,
    }

    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "prepare":
            return print_result(prepare_plans())

        if action == "create-tasks":
            if len(sys.argv) < 3:
                raise ValueError("Plan ID is required")
            return print_result(create_tasks(sys.argv[2]))

        if action == "list":
            return print_result(list_plans())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_execution_plan_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "decision_execution_planner_error",
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

chmod +x "$AGENTS/decision_execution_planner.py"

cat > "$CTL/executionplanctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "decision_execution_planner.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/executionplanctl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/decision_execution_planner.py" \
  "$CTL/executionplanctl"

echo "[2/5] Preparing execution plans..."
python "$CTL/executionplanctl" prepare

echo "[3/5] Checking planner..."
python "$CTL/executionplanctl" list
python "$CTL/executionplanctl" status

echo "[4/5] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "decision_execution_planner.py",
    root / "companyos" / "executionplanctl",
    root / "ceo_memory" / "decision_execution_config.json",
    root / "ceo_memory" / "decision_execution_plans.json",
    root / "ceo_memory" / "decision_execution_health.json",
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
        "automatic_task_execution",
        "automatic_customer_contact",
        "automatic_external_execution",
        "automatic_publication",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    plans = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("plans", [])

    for plan in plans:
        if plan.get("automatic_task_execution") is not False:
            errors.append("Automatic task execution was enabled")
            break

        if plan.get("automatic_external_execution") is not False:
            errors.append("External execution was enabled")
            break

        if not plan.get("steps"):
            errors.append("Execution plan has no steps")
            break

except Exception as exc:
    errors.append(f"Plan data error: {exc}")

print("--------------------------------------------")
print("Phase 17 Step 5 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo "[5/5] Complete."

echo
echo "============================================================"
echo " PHASE 17 STEP 5 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/executionplanctl prepare"
echo "  python companyos/executionplanctl list"
echo "  python companyos/executionplanctl create-tasks PLAN_ID"
echo "  python companyos/executionplanctl status"
