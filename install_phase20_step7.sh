#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase20_step7_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 20 Step 7 - Adaptive Action Prioritization Engine"
echo "============================================================"

for f in \
  "$AGENTS/adaptive_priority_engine.py" \
  "$CTL/adaptivepriorityctl" \
  "$MEM/adaptive_priority_config.json" \
  "$MEM/adaptive_priority_state.json" \
  "$MEM/adaptive_priority_report.json" \
  "$MEM/adaptive_priority_health.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/adaptive_priority_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_priority_adjustment": true,
  "success_bonus": 10,
  "failure_penalty": 20,
  "blocked_penalty": 5,
  "maximum_adjustment": 30,
  "minimum_priority": 1,
  "maximum_priority": 100,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/adaptive_priority_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "adaptive_priority_config.json"
ACTION_QUEUE = MEM / "action_queue_report.json"
DISPATCH = MEM / "action_dispatcher_report.json"
FEEDBACK = MEM / "dispatcher_feedback_report.json"

STATE = MEM / "adaptive_priority_state.json"
REPORT = MEM / "adaptive_priority_report.json"
HEALTH = MEM / "adaptive_priority_health.json"

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

def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))

def run() -> dict[str, Any]:
    cfg = load(CFG, {})
    queue = load(ACTION_QUEUE, {}).get("queue", [])
    dispatch = load(DISPATCH, {})
    feedback = load(FEEDBACK, {})

    success_bonus = int(cfg.get("success_bonus", 10))
    failure_penalty = int(cfg.get("failure_penalty", 20))
    blocked_penalty = int(cfg.get("blocked_penalty", 5))
    maximum_adjustment = int(cfg.get("maximum_adjustment", 30))
    minimum_priority = int(cfg.get("minimum_priority", 1))
    maximum_priority = int(cfg.get("maximum_priority", 100))

    outcomes = {}

    for item in dispatch.get("results", []):
        action = item.get("action")
        if not action:
            continue
        if item.get("success"):
            outcomes.setdefault(action, {"success": 0, "failure": 0, "blocked": 0})
            outcomes[action]["success"] += 1
        else:
            outcomes.setdefault(action, {"success": 0, "failure": 0, "blocked": 0})
            outcomes[action]["failure"] += 1

    for item in dispatch.get("blocked", []):
        action = item.get("action")
        if not action:
            continue
        outcomes.setdefault(action, {"success": 0, "failure": 0, "blocked": 0})
        outcomes[action]["blocked"] += 1

    repeated_failures = feedback.get("repeated_failures", {})

    adjusted = []

    for item in queue:
        action = item.get("action")
        base = int(item.get("priority", 50))
        stats = outcomes.get(action, {"success": 0, "failure": 0, "blocked": 0})

        adjustment = (
            stats["success"] * success_bonus
            - stats["failure"] * failure_penalty
            - stats["blocked"] * blocked_penalty
        )

        if int(repeated_failures.get(action, 0)) > 0:
            adjustment -= failure_penalty

        adjustment = clamp(
            adjustment,
            -maximum_adjustment,
            maximum_adjustment
        )

        adaptive = clamp(
            base + adjustment,
            minimum_priority,
            maximum_priority
        )

        adjusted.append({
            "action": action,
            "base_priority": base,
            "adjustment": adjustment,
            "adaptive_priority": adaptive,
            "reason": item.get("reason"),
            "outcomes": stats
        })

    adjusted.sort(
        key=lambda x: x["adaptive_priority"],
        reverse=True
    )

    report = {
        "generated_at": now(),
        "adaptive_priorities": adjusted,
        "top_action": adjusted[0]["action"] if adjusted else None,
        "top_priority": adjusted[0]["adaptive_priority"] if adjusted else None,
        "automatic_external_write": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_updated_at": now(),
        "action_count": len(adjusted),
        "top_action": report["top_action"],
        "top_priority": report["top_priority"]
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "action_count": len(adjusted)
    })

    return {
        "success": True,
        "status": "adaptive_prioritization_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "adaptive_priority_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = run()
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

chmod +x "$AGENTS/adaptive_priority_engine.py"

cat > "$CTL/adaptivepriorityctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "adaptive_priority_engine.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/adaptivepriorityctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/adaptive_priority_engine.py" "$CTL/adaptivepriorityctl"

echo "[2/6] Running adaptive prioritization..."
python "$CTL/adaptivepriorityctl" run

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "adaptive-action-prioritization",
    "enabled": True,
    "interval_seconds": 21600,
    "command": ["python", "companyos/adaptivepriorityctl", "run"]
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

echo "[5/6] Checking adaptive priority status..."
python "$CTL/adaptivepriorityctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "adaptive_priority_engine.py",
    root / "companyos" / "adaptivepriorityctl",
    root / "ceo_memory" / "adaptive_priority_config.json",
    root / "ceo_memory" / "adaptive_priority_state.json",
    root / "ceo_memory" / "adaptive_priority_report.json",
    root / "ceo_memory" / "adaptive_priority_health.json",
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
        "automatic_merge",
        "automatic_deploy",
        "automatic_publication",
        "automatic_spending",
        "automatic_destructive_actions"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    report = json.loads(required[4].read_text())
    if "adaptive_priorities" not in report:
        errors.append("Adaptive priority report missing adaptive_priorities")

    sched = json.loads(required[6].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "adaptive-action-prioritization"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Adaptive priority scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 7 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 7 INSTALLED"
echo " ADAPTIVE ACTION PRIORITIZATION ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/adaptivepriorityctl run"
echo "  python companyos/adaptivepriorityctl status"
