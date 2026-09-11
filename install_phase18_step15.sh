#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase18_step15_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$BACKUP"

echo "============================================================"
echo " Phase 18 Step 15 - Autonomous Mission Control"
echo "============================================================"

for file in \
  "$AGENTS/mission_control_engine.py" \
  "$CTL/missionctl" \
  "$MEMORY/mission_control_config.json" \
  "$MEMORY/mission_control_state.json" \
  "$MEMORY/mission_control_brief.json" \
  "$MEMORY/mission_control_health.json" \
  "$MEMORY/mission_control_audit.json" \
  "$MEMORY/autonomous_operations_config.json"
do
  [ -f "$file" ] && cp -a "$file" "$BACKUP/"
done

cat > "$MEMORY/mission_control_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_system_summary": true,
  "automatic_priority_summary": true,
  "automatic_goal_summary": true,
  "automatic_health_summary": true,
  "automatic_recovery_summary": true,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/mission_control_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "mission_control_config.json"
STATE = MEMORY / "mission_control_state.json"
BRIEF = MEMORY / "mission_control_brief.json"
HEALTH = MEMORY / "mission_control_health.json"
AUDIT = MEMORY / "mission_control_audit.json"

SOURCES = {
    "operations": MEMORY / "autonomous_operations_health.json",
    "watchdog": MEMORY / "watchdog_health.json",
    "orchestrator": MEMORY / "autonomous_orchestrator_health.json",
    "recovery": MEMORY / "exception_recovery_health.json",
    "learning": MEMORY / "learning_feedback_health.json",
    "resources": MEMORY / "resource_workload_health.json",
    "actions": MEMORY / "internal_action_health.json",
    "supervisor": MEMORY / "autonomous_health_report.json",
    "priorities": MEMORY / "executive_priority_rankings.json",
    "goals": MEMORY / "goal_strategy_goals.json",
    "forecast": MEMORY / "business_forecasting_briefing.json",
}


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


def audit(action: str, result: dict[str, Any]) -> None:
    records = load(AUDIT, [])
    if not isinstance(records, list):
        records = []
    records.append({"timestamp": now(), "action": action, "result": result})
    save(AUDIT, records[-1000:])


def build() -> dict[str, Any]:
    config = load(CONFIG, {})
    if not config.get("enabled", True):
        result = {"success": False, "status": "mission_control_disabled"}
        audit("build", result)
        return result

    data = {name: load(path, {}) for name, path in SOURCES.items()}

    priorities = data["priorities"].get("rankings", {}).get("priorities", [])
    goals = data["goals"].get("goals", [])
    forecast = data["forecast"].get("briefing", {})
    supervisor = data["supervisor"]

    health_components = {}
    unhealthy = []

    for name in [
        "operations",
        "watchdog",
        "orchestrator",
        "recovery",
        "learning",
        "resources",
        "actions",
    ]:
        healthy = data[name].get("healthy")
        health_components[name] = healthy
        if healthy is False:
            unhealthy.append(name)

    remaining_issues = supervisor.get("remaining_issues", 0)

    state = {
        "generated_at": now(),
        "system_health": health_components,
        "unhealthy_components": unhealthy,
        "remaining_supervisor_issues": remaining_issues,
        "top_priorities": priorities[:5],
        "top_goals": goals[:5],
        "forecast_headline": forecast.get("headline"),
        "forecast_confidence_percent": forecast.get("confidence_percent"),
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False
    }
    save(STATE, state)

    attention = []
    if unhealthy:
        attention.append("Unhealthy components: " + ", ".join(unhealthy))
    if remaining_issues:
        attention.append(f"{remaining_issues} health issue(s) remain unresolved.")
    if not priorities:
        attention.append("No executive priorities are currently available.")
    if not goals:
        attention.append("No active autonomous goals are currently available.")
    if not attention:
        attention.append("All monitored systems are operating normally.")

    brief = {
        "generated_at": now(),
        "headline": "CompanyOS Mission Control",
        "overall_status": "attention_required" if unhealthy or remaining_issues else "operational",
        "attention": attention,
        "top_priorities": [x.get("title") for x in priorities[:5]],
        "top_goals": [x.get("title") for x in goals[:5]],
        "forecast": {
            "headline": forecast.get("headline"),
            "confidence_percent": forecast.get("confidence_percent")
        }
    }
    save(BRIEF, brief)

    save(HEALTH, {
        "healthy": not unhealthy and not remaining_issues,
        "last_generated_at": now(),
        "unhealthy_component_count": len(unhealthy),
        "remaining_issue_count": remaining_issues
    })

    result = {
        "success": True,
        "status": "mission_control_updated",
        "state": state,
        "brief": brief
    }
    audit("build", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "mission_control_status",
        "health": load(HEALTH, {}),
        "brief": load(BRIEF, {})
    }
    audit("status", result)
    return result


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    result = build() if action == "build" else status() if action == "status" else {
        "success": False,
        "status": "unknown_action",
        "allowed": ["build", "status"]
    }
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/mission_control_engine.py"

cat > "$CTL/missionctl" <<'PY'
#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "mission_control_engine.py"

raise SystemExit(subprocess.call(
    [sys.executable, str(agent), *sys.argv[1:]],
    cwd=root
))
PY

chmod +x "$CTL/missionctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/mission_control_engine.py" "$CTL/missionctl"

echo "[2/6] Building mission control..."
python "$CTL/missionctl" build

echo "[3/6] Adding mission control to scheduler..."
python - <<'PY'
import json
from pathlib import Path

root = Path.home() / "companyos"
path = root / "ceo_memory" / "autonomous_operations_config.json"
data = json.loads(path.read_text(encoding="utf-8"))
jobs = data.setdefault("jobs", [])

job = {
    "id": "mission-control",
    "enabled": True,
    "interval_seconds": 900,
    "command": ["python", "companyos/missionctl", "build"]
}

existing = next((x for x in jobs if x.get("id") == job["id"]), None)
if existing:
    existing.clear()
    existing.update(job)
else:
    jobs.append(job)

path.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(json.dumps({"success": True, "job_id": job["id"]}, indent=2))
PY

echo "[4/6] Restarting scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking mission control..."
python "$CTL/missionctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json, py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root/"agents"/"mission_control_engine.py",
    root/"companyos"/"missionctl",
    root/"ceo_memory"/"mission_control_config.json",
    root/"ceo_memory"/"mission_control_state.json",
    root/"ceo_memory"/"mission_control_brief.json",
    root/"ceo_memory"/"mission_control_health.json",
    root/"ceo_memory"/"autonomous_operations_config.json"
]

for p in required:
    if not p.exists():
        errors.append(f"Missing: {p}")
    elif p.stat().st_size <= 0:
        errors.append(f"Empty: {p}")

for p in required[:2]:
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as e:
        errors.append(f"Compile error: {e}")

try:
    cfg = json.loads(required[2].read_text())
    for field in [
        "automatic_customer_contact",
        "automatic_publication",
        "automatic_spending",
        "automatic_destructive_actions"
    ]:
        if cfg.get(field) is not False:
            errors.append(f"{field} must remain disabled")

    sched = json.loads(required[6].read_text())
    job = next((x for x in sched.get("jobs", []) if x.get("id") == "mission-control"), None)
    if not job or job.get("enabled") is not True:
        errors.append("Mission control scheduler job missing or disabled")
except Exception as e:
    errors.append(f"Verification error: {e}")

print("--------------------------------------------")
print("Phase 18 Step 15 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for e in errors:
    print("ERROR:", e)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 18 STEP 15 INSTALLED"
echo " AUTONOMOUS MISSION CONTROL ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/missionctl build"
echo "  python companyos/missionctl status"
echo
echo "Autonomous schedule:"
echo "  Mission control refreshes every 15 minutes"
