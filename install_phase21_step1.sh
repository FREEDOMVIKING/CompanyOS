#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 1 - Autonomous Strategic Goal Orchestrator"
echo "============================================================"

cat > "$MEM/strategic_orchestrator_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_goal_refresh": true,
  "automatic_priority_refresh": true,
  "automatic_forecast_refresh": true,
  "automatic_closed_loop_trigger": true,
  "maximum_goals_per_cycle": 10,
  "minimum_goal_score": 50,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_git_reset": false,
  "automatic_git_clean": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/strategic_goal_orchestrator.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "strategic_orchestrator_config.json"
GOALS = MEM / "goal_strategy_goals.json"
PRIORITIES = MEM / "feedback_priority_report.json"
FORECAST = MEM / "business_forecasting_report.json"

STATE = MEM / "strategic_orchestrator_state.json"
REPORT = MEM / "strategic_orchestrator_report.json"
HEALTH = MEM / "strategic_orchestrator_health.json"

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

def call(args: list[str], timeout: int = 600) -> dict[str, Any]:
    try:
        p = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout
        )
        return {
            "success": p.returncode == 0,
            "return_code": p.returncode,
            "stdout": p.stdout[-3000:],
            "stderr": p.stderr[-1500:]
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def orchestrate() -> dict[str, Any]:
    cfg = load(CFG, {})
    steps = []

    if cfg.get("automatic_goal_refresh", True):
        steps.append({
            "step": "refresh_goals",
            "result": call(["python", "companyos/goalctl", "generate"])
        })

    if cfg.get("automatic_priority_refresh", True):
        steps.append({
            "step": "refresh_priorities",
            "result": call(["python", "companyos/feedbackpriorityctl", "integrate"])
        })

    if cfg.get("automatic_forecast_refresh", True):
        steps.append({
            "step": "refresh_forecast",
            "result": call(["python", "companyos/forecastctl", "forecast"])
        })

    goals_doc = load(GOALS, {})
    goals = goals_doc.get("goals", [])
    priorities = load(PRIORITIES, {}).get("integrated_priorities", [])
    forecast = load(FORECAST, {})

    max_goals = int(cfg.get("maximum_goals_per_cycle", 10))
    min_score = float(cfg.get("minimum_goal_score", 50))

    normalized_goals = []

    for index, goal in enumerate(goals[:max_goals], start=1):
        score = goal.get("score", goal.get("priority_score", goal.get("progress_score", 50)))
        try:
            score = float(score)
        except Exception:
            score = 50.0

        normalized_goals.append({
            "rank": index,
            "id": goal.get("id"),
            "title": goal.get("title") or goal.get("name"),
            "score": round(score, 2),
            "eligible_for_cycle": score >= min_score,
            "status": goal.get("status")
        })

    eligible_goals = [g for g in normalized_goals if g["eligible_for_cycle"]]

    if cfg.get("automatic_closed_loop_trigger", True):
        steps.append({
            "step": "closed_loop_cycle",
            "result": call(["python", "companyos/loopctl", "run"])
        })

    failures = [
        item["step"]
        for item in steps
        if not item.get("result", {}).get("success", False)
    ]

    report = {
        "generated_at": now(),
        "goals": normalized_goals,
        "eligible_goals": eligible_goals,
        "eligible_goal_count": len(eligible_goals),
        "priority_snapshot": priorities[:10],
        "forecast_snapshot": forecast,
        "steps": steps,
        "failed_steps": failures,
        "failure_count": len(failures),
        "automatic_external_write": False,
        "automatic_code_changes": False,
        "automatic_git_reset": False,
        "automatic_git_clean": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_cycle_at": now(),
        "eligible_goal_count": len(eligible_goals),
        "failure_count": len(failures),
        "top_goal": eligible_goals[0]["title"] if eligible_goals else None
    })
    save(HEALTH, {
        "healthy": len(failures) == 0,
        "last_checked_at": now(),
        "eligible_goal_count": len(eligible_goals),
        "failure_count": len(failures)
    })

    return {
        "success": len(failures) == 0,
        "status": "strategic_goal_orchestration_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "strategic_goal_orchestrator_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = orchestrate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["run", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/strategic_goal_orchestrator.py"

cat > "$CTL/strategyorchestratorctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "strategic_goal_orchestrator.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/strategyorchestratorctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/strategic_goal_orchestrator.py" "$CTL/strategyorchestratorctl"

echo "[2/6] Running strategic orchestration..."
python "$CTL/strategyorchestratorctl" run || true

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "strategic-goal-orchestrator",
    "enabled": True,
    "interval_seconds": 21600,
    "command": ["python", "companyos/strategyorchestratorctl", "run"]
}

existing = next((x for x in jobs if x.get("id") == job["id"]), None)

if existing:
    existing.clear()
    existing.update(job)
else:
    jobs.append(job)

p.write_text(json.dumps(d, indent=2), encoding="utf-8")
print(json.dumps({"success": True, "job_id": job["id"]}, indent=2))
PY

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking orchestrator status..."
python "$CTL/strategyorchestratorctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "strategic_goal_orchestrator.py",
    root / "companyos" / "strategyorchestratorctl",
    root / "ceo_memory" / "strategic_orchestrator_config.json",
    root / "ceo_memory" / "strategic_orchestrator_state.json",
    root / "ceo_memory" / "strategic_orchestrator_report.json",
    root / "ceo_memory" / "strategic_orchestrator_health.json",
    root / "ceo_memory" / "autonomous_operations_config.json"
]

for path in required:
    if not path.exists() or path.stat().st_size <= 0:
        errors.append(f"Missing/empty: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(str(exc))

try:
    cfg = json.loads(required[2].read_text())

    for key in [
        "automatic_external_write",
        "automatic_code_changes",
        "automatic_git_reset",
        "automatic_git_clean",
        "automatic_merge",
        "automatic_deploy",
        "automatic_publication",
        "automatic_spending",
        "automatic_destructive_actions"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    sched = json.loads(required[6].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "strategic-goal-orchestrator"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Strategic goal orchestrator scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 21 Step 1 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 1 INSTALLED"
echo " AUTONOMOUS STRATEGIC GOAL ORCHESTRATOR ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/strategyorchestratorctl run"
echo "  python companyos/strategyorchestratorctl status"
