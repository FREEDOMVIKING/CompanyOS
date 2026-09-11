#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase17_step8_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$BACKUP"

echo "============================================================"
echo " Phase 17 Step 8 - Performance Analytics Engine"
echo "============================================================"

for file in \
  "$AGENTS/performance_analytics_engine.py" \
  "$CTL/performancectl" \
  "$MEMORY/performance_analytics_config.json" \
  "$MEMORY/performance_analytics_metrics.json" \
  "$MEMORY/performance_analytics_report.json" \
  "$MEMORY/performance_analytics_health.json" \
  "$MEMORY/performance_analytics_audit.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/performance_analytics_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_analysis": true,
  "automatic_metric_collection": true,
  "automatic_report_generation": true,
  "automatic_code_changes": false,
  "automatic_task_execution": false,
  "automatic_customer_contact": false,
  "automatic_external_execution": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "owner_approval_required": true
}
JSON

cat > "$AGENTS/performance_analytics_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "performance_analytics_config.json"
METRICS = MEMORY / "performance_analytics_metrics.json"
REPORT = MEMORY / "performance_analytics_report.json"
HEALTH = MEMORY / "performance_analytics_health.json"
AUDIT = MEMORY / "performance_analytics_audit.json"

TASKS = MEMORY / "product_execution_tasks.json"
DECISIONS = MEMORY / "ceo_decision_queue.json"
PLANS = MEMORY / "decision_execution_plans.json"
PROJECTS = MEMORY / "project_registry.json"
INVOICES = MEMORY / "invoice_registry.json"
PRIORITIES = MEMORY / "executive_priority_rankings.json"
IMPROVEMENTS = MEMORY / "continuous_improvement_backlog.json"


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


def number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def percent(part: float, whole: float) -> float:
    if whole <= 0:
        return 0.0
    return round((part / whole) * 100, 2)


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


def collect() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "performance_analytics_engine_disabled",
        }
        audit("collect", result)
        return result

    tasks = load_json(TASKS, {}).get("tasks", [])
    decisions = load_json(DECISIONS, {}).get("decisions", [])
    plans = load_json(PLANS, {}).get("plans", [])
    projects = load_json(PROJECTS, {}).get("projects", [])
    invoices = load_json(INVOICES, {}).get("invoices", [])
    priorities = load_json(
        PRIORITIES,
        {},
    ).get("rankings", {}).get("priorities", [])
    improvements = load_json(IMPROVEMENTS, {}).get("items", [])

    task_total = len(tasks)
    task_completed = sum(
        1 for item in tasks
        if item.get("status") == "completed"
    )
    task_pending = sum(
        1 for item in tasks
        if item.get("status") == "pending"
    )

    decision_total = len(decisions)
    decision_pending = sum(
        1 for item in decisions
        if item.get("status") == "pending"
    )
    decision_approved = sum(
        1 for item in decisions
        if item.get("status") == "approved"
    )

    plan_total = len(plans)
    plan_completed = sum(
        1 for item in plans
        if item.get("status") == "completed"
    )
    plan_ready = sum(
        1 for item in plans
        if item.get("status") == "ready"
    )

    project_total = len(projects)
    project_completed = sum(
        1 for item in projects
        if item.get("status") == "completed"
    )
    project_blocked = sum(
        1 for item in projects
        if item.get("status") in {"blocked", "waiting"}
    )

    outstanding_invoices = [
        item for item in invoices
        if number(item.get("balance_due"), 0) > 0
        and item.get("status") != "void"
    ]
    outstanding_value = round(
        sum(number(item.get("balance_due"), 0) for item in outstanding_invoices),
        2,
    )

    critical_priorities = sum(
        1 for item in priorities
        if item.get("priority_band") == "critical"
    )
    high_priorities = sum(
        1 for item in priorities
        if item.get("priority_band") == "high"
    )

    proposed_improvements = sum(
        1 for item in improvements
        if item.get("status") == "proposed"
    )
    approved_improvements = sum(
        1 for item in improvements
        if item.get("status") == "approved"
    )
    completed_improvements = sum(
        1 for item in improvements
        if item.get("status") == "completed"
    )

    metrics = {
        "generated_at": now(),
        "tasks": {
            "total": task_total,
            "completed": task_completed,
            "pending": task_pending,
            "completion_rate_percent": percent(task_completed, task_total),
        },
        "decisions": {
            "total": decision_total,
            "pending": decision_pending,
            "approved": decision_approved,
            "approval_rate_percent": percent(decision_approved, decision_total),
        },
        "execution_plans": {
            "total": plan_total,
            "ready": plan_ready,
            "completed": plan_completed,
            "completion_rate_percent": percent(plan_completed, plan_total),
        },
        "projects": {
            "total": project_total,
            "completed": project_completed,
            "blocked_or_waiting": project_blocked,
            "completion_rate_percent": percent(project_completed, project_total),
        },
        "finance": {
            "outstanding_invoice_count": len(outstanding_invoices),
            "outstanding_value": outstanding_value,
        },
        "priorities": {
            "total": len(priorities),
            "critical": critical_priorities,
            "high": high_priorities,
        },
        "improvements": {
            "total": len(improvements),
            "proposed": proposed_improvements,
            "approved": approved_improvements,
            "completed": completed_improvements,
        },
        "automatic_code_changes": False,
        "automatic_execution": False,
        "external_action_authorized": False,
    }

    save_json(
        METRICS,
        {
            "schema_version": 1,
            "metrics": metrics,
            "last_updated_at": now(),
        },
    )

    attention = []

    if task_total and metrics["tasks"]["completion_rate_percent"] < 50:
        attention.append("Task completion rate is below 50%.")

    if decision_pending >= 5:
        attention.append("Five or more CEO decisions are waiting for review.")

    if project_blocked > 0:
        attention.append("One or more projects are blocked or waiting.")

    if outstanding_value > 0:
        attention.append(
            f"${outstanding_value:,.2f} remains outstanding in receivables."
        )

    if critical_priorities > 0:
        attention.append(
            f"{critical_priorities} critical priority item(s) require attention."
        )

    if not attention:
        attention.append("No major operating performance issue was detected.")

    health_score = 100.0
    health_score -= min(task_pending * 2.0, 20.0)
    health_score -= min(decision_pending * 2.5, 20.0)
    health_score -= min(project_blocked * 10.0, 30.0)
    health_score -= min(critical_priorities * 5.0, 20.0)
    health_score = round(max(0.0, health_score), 2)

    report = {
        "generated_at": now(),
        "headline": f"CompanyOS performance health score: {health_score}/100",
        "health_score": health_score,
        "attention_items": attention,
        "key_metrics": metrics,
        "recommended_focus": attention[:5],
        "automatic_code_changes": False,
        "automatic_task_execution": False,
        "automatic_external_execution": False,
        "automatic_spending": False,
    }

    save_json(
        REPORT,
        {
            "schema_version": 1,
            "report": report,
            "last_updated_at": now(),
        },
    )

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_collected_at": now(),
            "health_score": health_score,
            "attention_item_count": len(attention),
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "performance_analytics_complete",
        "health_score": health_score,
        "metrics": metrics,
        "report": report,
    }
    audit("collect", result)
    return result


def show_metrics() -> dict[str, Any]:
    data = load_json(METRICS, {}).get("metrics")
    result = {
        "success": bool(data),
        "status": "performance_analytics_metrics",
        "metrics": data,
    }
    audit("metrics", result)
    return result


def show_report() -> dict[str, Any]:
    data = load_json(REPORT, {}).get("report")
    result = {
        "success": bool(data),
        "status": "performance_analytics_report",
        "report": data,
    }
    audit("report", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "performance_analytics_engine_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_analysis": config.get(
            "automatic_internal_analysis", False
        ),
        "automatic_metric_collection": config.get(
            "automatic_metric_collection", False
        ),
        "automatic_report_generation": config.get(
            "automatic_report_generation", False
        ),
        "automatic_code_changes": config.get(
            "automatic_code_changes", False
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
        if action == "collect":
            return print_result(collect())

        if action == "metrics":
            return print_result(show_metrics())

        if action == "report":
            return print_result(show_report())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_performance_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "performance_analytics_error",
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

chmod +x "$AGENTS/performance_analytics_engine.py"

cat > "$CTL/performancectl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "performance_analytics_engine.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/performancectl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/performance_analytics_engine.py" \
  "$CTL/performancectl"

echo "[2/5] Collecting performance metrics..."
python "$CTL/performancectl" collect

echo "[3/5] Checking outputs..."
python "$CTL/performancectl" metrics
python "$CTL/performancectl" report
python "$CTL/performancectl" status

echo "[4/5] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "performance_analytics_engine.py",
    root / "companyos" / "performancectl",
    root / "ceo_memory" / "performance_analytics_config.json",
    root / "ceo_memory" / "performance_analytics_metrics.json",
    root / "ceo_memory" / "performance_analytics_report.json",
    root / "ceo_memory" / "performance_analytics_health.json",
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
    metrics = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("metrics", {})

    for field in [
        "tasks",
        "decisions",
        "execution_plans",
        "projects",
        "finance",
        "priorities",
        "improvements",
    ]:
        if field not in metrics:
            errors.append(f"Metrics missing field: {field}")

    report = json.loads(
        required[4].read_text(encoding="utf-8")
    ).get("report", {})

    for field in [
        "headline",
        "health_score",
        "attention_items",
        "key_metrics",
        "recommended_focus",
    ]:
        if field not in report:
            errors.append(f"Report missing field: {field}")

    if report.get("automatic_external_execution") is not False:
        errors.append("External execution was enabled")

    if report.get("automatic_spending") is not False:
        errors.append("Automatic spending was enabled")

except Exception as exc:
    errors.append(f"Performance data error: {exc}")

print("--------------------------------------------")
print("Phase 17 Step 8 verification")
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
echo " PHASE 17 STEP 8 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/performancectl collect"
echo "  python companyos/performancectl metrics"
echo "  python companyos/performancectl report"
echo "  python companyos/performancectl status"
