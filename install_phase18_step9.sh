#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase18_step9_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 9 - Autonomous Goal & Strategy Engine"
echo "============================================================"

for file in \
  "$AGENTS/goal_strategy_engine.py" \
  "$CTL/goalctl" \
  "$MEMORY/goal_strategy_config.json" \
  "$MEMORY/goal_strategy_goals.json" \
  "$MEMORY/goal_strategy_plan.json" \
  "$MEMORY/goal_strategy_health.json" \
  "$MEMORY/goal_strategy_audit.json" \
  "$MEMORY/autonomous_operations_config.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/goal_strategy_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_goal_generation": true,
  "automatic_goal_prioritization": true,
  "automatic_internal_strategy_updates": true,
  "automatic_internal_task_recommendations": true,
  "maximum_active_goals": 10,
  "review_interval_hours": 6,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/goal_strategy_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "goal_strategy_config.json"
GOALS = MEMORY / "goal_strategy_goals.json"
PLAN = MEMORY / "goal_strategy_plan.json"
HEALTH = MEMORY / "goal_strategy_health.json"
AUDIT = MEMORY / "goal_strategy_audit.json"

PRIORITIES = MEMORY / "executive_priority_rankings.json"
PERFORMANCE = MEMORY / "performance_analytics_report.json"
FORECAST = MEMORY / "business_forecasting_briefing.json"
IMPROVEMENTS = MEMORY / "continuous_improvement_briefing.json"
DECISIONS = MEMORY / "ceo_decision_queue.json"


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


def score_goal(impact: float, urgency: float, confidence: float) -> float:
    return round(
        max(0.0, min(100.0, impact * 0.45 + urgency * 0.35 + confidence * 0.20)),
        2,
    )


def generate_goals() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {"success": False, "status": "goal_strategy_engine_disabled"}
        audit("generate", result)
        return result

    priorities = load_json(PRIORITIES, {}).get("rankings", {}).get("priorities", [])
    performance = load_json(PERFORMANCE, {}).get("report", {})
    forecast = load_json(FORECAST, {}).get("briefing", {})
    improvements = load_json(IMPROVEMENTS, {}).get("briefing", {})
    decisions = load_json(DECISIONS, {}).get("decisions", [])

    goals = []

    for item in priorities[:5]:
        score = score_goal(
            float(item.get("score", 50)),
            float(item.get("urgency", 50)),
            85.0,
        )
        goals.append({
            "id": f"priority-{item.get('source_id') or item.get('id')}",
            "title": item.get("title") or "Priority goal",
            "source": "executive_priority",
            "category": item.get("category"),
            "objective": item.get("description"),
            "score": score,
            "status": "active",
            "owner_approval_required_for_external_action": True,
            "automatic_external_execution": False,
            "created_at": now(),
        })

    health_score = performance.get("health_score")
    if isinstance(health_score, (int, float)) and health_score < 80:
        goals.append({
            "id": "improve-operating-health",
            "title": "Improve operating health score",
            "source": "performance_analytics",
            "category": "operations",
            "objective": f"Raise operating health above 80 from {health_score}.",
            "score": score_goal(85, 80, 95),
            "status": "active",
            "owner_approval_required_for_external_action": True,
            "automatic_external_execution": False,
            "created_at": now(),
        })

    expected = (
        forecast.get("scenarios", {}).get("expected")
        if isinstance(forecast, dict) else None
    )
    if expected is not None:
        goals.append({
            "id": "protect-expected-cash-inflow",
            "title": "Protect expected cash inflow",
            "source": "business_forecast",
            "category": "finance",
            "objective": f"Protect the expected forecast value of ${float(expected):,.2f}.",
            "score": score_goal(90, 75, 80),
            "status": "active",
            "owner_approval_required_for_external_action": True,
            "automatic_external_execution": False,
            "created_at": now(),
        })

    for item in improvements.get("top_recommendations", [])[:3]:
        goals.append({
            "id": f"improvement-{item.get('id')}",
            "title": item.get("title") or "Continuous improvement goal",
            "source": "continuous_improvement",
            "category": item.get("category"),
            "objective": item.get("recommendation"),
            "score": float(item.get("score", 60)),
            "status": "active",
            "owner_approval_required_for_external_action": True,
            "automatic_external_execution": False,
            "created_at": now(),
        })

    pending_decisions = [d for d in decisions if d.get("status") == "pending"]
    if pending_decisions:
        goals.append({
            "id": "clear-pending-decisions",
            "title": "Clear pending CEO decisions",
            "source": "ceo_decision_queue",
            "category": "governance",
            "objective": f"Review {len(pending_decisions)} pending decision(s).",
            "score": score_goal(78, 88, 95),
            "status": "active",
            "owner_approval_required_for_external_action": True,
            "automatic_external_execution": False,
            "created_at": now(),
        })

    deduped = {}
    for goal in goals:
        key = goal["id"]
        if key not in deduped or goal["score"] > deduped[key]["score"]:
            deduped[key] = goal

    goals = sorted(
        deduped.values(),
        key=lambda item: float(item.get("score", 0)),
        reverse=True,
    )[: int(config.get("maximum_active_goals", 10))]

    for index, goal in enumerate(goals, start=1):
        goal["rank"] = index

    save_json(
        GOALS,
        {
            "schema_version": 1,
            "generated_at": now(),
            "goals": goals,
            "count": len(goals),
        },
    )

    strategy_steps = []
    for goal in goals:
        strategy_steps.append({
            "goal_id": goal["id"],
            "goal_title": goal["title"],
            "rank": goal["rank"],
            "steps": [
                "Review current evidence and constraints",
                "Define the highest-value internal next action",
                "Create or update internal execution tasks",
                "Measure progress against the goal",
                "Re-rank after new performance data arrives",
            ],
            "automatic_internal_execution_allowed": True,
            "automatic_external_execution_allowed": False,
        })

    plan = {
        "generated_at": now(),
        "strategy": strategy_steps,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False,
    }
    save_json(PLAN, plan)

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_generated_at": now(),
            "goal_count": len(goals),
            "top_goal": goals[0]["title"] if goals else None,
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "goal_strategy_generated",
        "goal_count": len(goals),
        "goals": goals,
        "plan": plan,
    }
    audit("generate", result)
    return result


def show_goals() -> dict[str, Any]:
    data = load_json(GOALS, {})
    result = {
        "success": bool(data),
        "status": "goal_strategy_goals",
        "data": data,
    }
    audit("goals", result)
    return result


def show_plan() -> dict[str, Any]:
    data = load_json(PLAN, {})
    result = {
        "success": bool(data),
        "status": "goal_strategy_plan",
        "data": data,
    }
    audit("plan", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "goal_strategy_status",
        "config": load_json(CONFIG, {}),
        "health": load_json(HEALTH, {}),
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "generate":
            return print_result(generate_goals())
        if action == "goals":
            return print_result(show_goals())
        if action == "plan":
            return print_result(show_plan())
        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_goal_action",
            "action": action,
            "allowed": ["generate", "goals", "plan", "status"],
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "goal_strategy_error",
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

chmod +x "$AGENTS/goal_strategy_engine.py"

cat > "$CTL/goalctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "goal_strategy_engine.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/goalctl"

echo "[1/6] Compiling..."
python -m py_compile \
  "$AGENTS/goal_strategy_engine.py" \
  "$CTL/goalctl"

echo "[2/6] Generating goals and strategy..."
python "$CTL/goalctl" generate

echo "[3/6] Adding goal strategy job to autonomous scheduler..."
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
    "id": "goal-strategy",
    "enabled": True,
    "interval_seconds": 21600,
    "command": ["python", "companyos/goalctl", "generate"]
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

echo "[5/6] Checking goal strategy..."
python "$CTL/goalctl" status
python "$CTL/operationsctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "goal_strategy_engine.py",
    root / "companyos" / "goalctl",
    root / "ceo_memory" / "goal_strategy_config.json",
    root / "ceo_memory" / "goal_strategy_goals.json",
    root / "ceo_memory" / "goal_strategy_plan.json",
    root / "ceo_memory" / "goal_strategy_health.json",
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

    goals = json.loads(required[3].read_text(encoding="utf-8"))
    if not goals.get("goals"):
        errors.append("No goals were generated")

    plan = json.loads(required[4].read_text(encoding="utf-8"))
    if not plan.get("strategy"):
        errors.append("No strategy plan was generated")

    scheduler = json.loads(required[6].read_text(encoding="utf-8"))
    job = next(
        (
            item for item in scheduler.get("jobs", [])
            if item.get("id") == "goal-strategy"
        ),
        None,
    )

    if not job:
        errors.append("Goal strategy scheduler job missing")
    elif job.get("enabled") is not True:
        errors.append("Goal strategy scheduler job disabled")

except Exception as exc:
    errors.append(f"Verification data error: {exc}")

print("--------------------------------------------")
print("Phase 18 Step 9 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 STEP 9 INSTALLED"
echo " AUTONOMOUS GOAL & STRATEGY ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/goalctl generate"
echo "  python companyos/goalctl goals"
echo "  python companyos/goalctl plan"
echo "  python companyos/goalctl status"
echo
echo "Autonomous schedule:"
echo "  Goals and strategy regenerate every 6 hours"
