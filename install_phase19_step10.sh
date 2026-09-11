#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase19_step10_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 19 Step 10 - Autonomous Action Queue Coordinator"
echo "============================================================"

for f in \
 "$AGENTS/action_queue_coordinator.py" \
 "$CTL/actionqueuectl" \
 "$MEM/action_queue_config.json" \
 "$MEM/action_queue_state.json" \
 "$MEM/action_queue_report.json" \
 "$MEM/action_queue_health.json" \
 "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/action_queue_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_queue_build": true,
  "automatic_internal_dispatch": true,
  "maximum_actions_per_cycle": 10,
  "minimum_priority_score": 50,
  "require_preflight_for_git_related_actions": true,
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false,
  "credential_export": false,
  "private_key_export": false
}
JSON

cat > "$AGENTS/action_queue_coordinator.py" <<'PY'
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

CFG = MEM / "action_queue_config.json"
STATE = MEM / "action_queue_state.json"
REPORT = MEM / "action_queue_report.json"
HEALTH = MEM / "action_queue_health.json"

PREFLIGHT = MEM / "preflight_gate_report.json"
MISSION = MEM / "mission_control_brief.json"
GOALS = MEM / "goal_strategy_goals.json"
OUTCOMES = MEM / "outcome_tracker_report.json"
GH_INTEL = MEM / "github_intelligence_report.json"

ACTION_MAP = {
    "refresh-priorities": ["python", "companyos/priorityctl", "rank"],
    "refresh-decisions": ["python", "companyos/decisionctl", "prepare"],
    "refresh-forecast": ["python", "companyos/forecastctl", "forecast"],
    "refresh-brief": ["python", "companyos/briefctl", "generate"],
    "refresh-goals": ["python", "companyos/goalctl", "generate"],
    "run-learning": ["python", "companyos/learningctl", "learn"],
    "run-health": ["python", "companyos/healthctl", "run"],
    "run-readiness": ["python", "companyos/readinessctl", "check"],
    "run-outcomes": ["python", "companyos/outcomectl", "measure"]
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

def run(command: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=300
        )
        return {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-2500:],
            "stderr": proc.stderr[-1200:]
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def build_queue() -> list[dict[str, Any]]:
    preflight = load(PREFLIGHT, {})
    mission = load(MISSION, {})
    goals = load(GOALS, {}).get("goals", [])
    outcomes = load(OUTCOMES, {})
    gh = load(GH_INTEL, {})

    queue: list[dict[str, Any]] = []

    if preflight.get("decision") == "blocked":
        queue.append({
            "action": "run-health",
            "priority": 95,
            "reason": "Preflight is blocked; verify system health before further work."
        })

    attention = mission.get("attention", [])
    if attention and attention != ["All monitored systems are operating normally."]:
        queue.append({
            "action": "run-readiness",
            "priority": 90,
            "reason": "Mission control reports items requiring attention."
        })

    needs_attention = outcomes.get("needs_attention", [])
    if needs_attention:
        queue.append({
            "action": "run-learning",
            "priority": 85,
            "reason": f"{len(needs_attention)} goal outcome(s) need attention."
        })
        queue.append({
            "action": "refresh-goals",
            "priority": 80,
            "reason": "Refresh goals after learning from underperforming outcomes."
        })

    if goals:
        queue.append({
            "action": "refresh-forecast",
            "priority": 70,
            "reason": "Keep forecast aligned with active goals."
        })

    if "uncommitted_changes" in gh.get("signals", []):
        queue.append({
            "action": "refresh-brief",
            "priority": 65,
            "reason": "Summarize current repository state before owner review."
        })

    queue.extend([
        {
            "action": "refresh-priorities",
            "priority": 60,
            "reason": "Maintain current executive ordering."
        },
        {
            "action": "refresh-decisions",
            "priority": 55,
            "reason": "Keep CEO decision queue synchronized."
        },
        {
            "action": "run-outcomes",
            "priority": 50,
            "reason": "Refresh measurable outcomes for the feedback loop."
        }
    ])

    seen = set()
    deduped = []
    for item in sorted(queue, key=lambda x: int(x["priority"]), reverse=True):
        if item["action"] in seen:
            continue
        seen.add(item["action"])
        deduped.append(item)

    return deduped

def coordinate() -> dict[str, Any]:
    cfg = load(CFG, {})
    if not cfg.get("enabled", True):
        return {"success": False, "status": "action_queue_coordinator_disabled"}

    queue = build_queue()
    minimum = int(cfg.get("minimum_priority_score", 50))
    maximum = int(cfg.get("maximum_actions_per_cycle", 10))

    selected = [x for x in queue if int(x.get("priority", 0)) >= minimum][:maximum]
    results = []

    for item in selected:
        command = ACTION_MAP.get(item["action"])
        if not command:
            results.append({
                "action": item["action"],
                "success": False,
                "error": "action_not_mapped"
            })
            continue

        result = run(command)
        results.append({
            "action": item["action"],
            "priority": item["priority"],
            "reason": item["reason"],
            "result": result,
            "success": result.get("success", False)
        })

    failures = [x for x in results if not x.get("success")]

    report = {
        "generated_at": now(),
        "queue": queue,
        "selected": selected,
        "results": results,
        "failure_count": len(failures),
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "generated_at": now(),
        "queued_count": len(queue),
        "executed_count": len(results),
        "failure_count": len(failures)
    })
    save(HEALTH, {
        "healthy": len(failures) == 0,
        "last_run_at": now(),
        "queued_count": len(queue),
        "executed_count": len(results),
        "failure_count": len(failures)
    })

    return {
        "success": len(failures) == 0,
        "status": "action_queue_cycle_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "action_queue_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = coordinate()
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

chmod +x "$AGENTS/action_queue_coordinator.py"

cat > "$CTL/actionqueuectl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "action_queue_coordinator.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/actionqueuectl"

echo "[1/5] Compiling..."
python -m py_compile "$AGENTS/action_queue_coordinator.py" "$CTL/actionqueuectl"

echo "[2/5] Running autonomous action queue..."
python "$CTL/actionqueuectl" run

echo "[3/5] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "action-queue-coordinator",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/actionqueuectl", "run"]
}

existing = next((x for x in jobs if x.get("id") == job["id"]), None)
if existing:
    existing.clear()
    existing.update(job)
else:
    jobs.append(job)

p.write_text(json.dumps(d, indent=2))
print(json.dumps({"success": True, "job_id": job["id"]}, indent=2))
PY

echo "[4/5] Restarting scheduler..."
python "$CTL/operationsctl" restart
python "$CTL/actionqueuectl" status

echo "[5/5] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

r = Path.home()/"companyos"
errors = []

req = [
    r/"agents"/"action_queue_coordinator.py",
    r/"companyos"/"actionqueuectl",
    r/"ceo_memory"/"action_queue_config.json",
    r/"ceo_memory"/"action_queue_state.json",
    r/"ceo_memory"/"action_queue_report.json",
    r/"ceo_memory"/"action_queue_health.json",
    r/"ceo_memory"/"autonomous_operations_config.json"
]

for p in req:
    if not p.exists() or p.stat().st_size <= 0:
        errors.append(f"Missing/empty: {p}")

for p in req[:2]:
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as exc:
        errors.append(str(exc))

try:
    cfg = json.loads(req[2].read_text())
    for key in [
        "automatic_external_write",
        "automatic_customer_contact",
        "automatic_publication",
        "automatic_spending",
        "automatic_destructive_actions",
        "credential_export",
        "private_key_export"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    sched = json.loads(req[6].read_text())
    job = next(
        (x for x in sched.get("jobs", [])
         if x.get("id") == "action-queue-coordinator"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Action queue scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 19 Step 10 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 19 STEP 10 INSTALLED"
echo " AUTONOMOUS ACTION QUEUE COORDINATOR ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/actionqueuectl run"
echo "  python companyos/actionqueuectl status"
echo
echo "Autonomous schedule:"
echo "  Coordinated internal action cycle runs every 30 minutes"
