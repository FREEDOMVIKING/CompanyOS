#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase20_step6_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 20 Step 6 - Autonomous Outcome Feedback Loop"
echo "============================================================"

for f in \
  "$AGENTS/dispatcher_feedback_loop.py" \
  "$CTL/dispatcherfeedbackctl" \
  "$MEM/dispatcher_feedback_config.json" \
  "$MEM/dispatcher_feedback_state.json" \
  "$MEM/dispatcher_feedback_report.json" \
  "$MEM/dispatcher_feedback_health.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/dispatcher_feedback_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_feedback_analysis": true,
  "automatic_learning_trigger": true,
  "automatic_priority_feedback": true,
  "failure_rate_threshold": 0.25,
  "repeat_failure_threshold": 2,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/dispatcher_feedback_loop.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "dispatcher_feedback_config.json"
DISPATCH = MEM / "action_dispatcher_report.json"
STATE = MEM / "dispatcher_feedback_state.json"
REPORT = MEM / "dispatcher_feedback_report.json"
HEALTH = MEM / "dispatcher_feedback_health.json"

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
        return {
            "success": False,
            "error": str(exc)
        }

def analyze() -> dict[str, Any]:
    cfg = load(CFG, {})
    dispatch = load(DISPATCH, {})
    results = dispatch.get("results", [])
    blocked = dispatch.get("blocked", [])

    executed = len(results)
    failed = sum(1 for x in results if not x.get("success"))
    succeeded = executed - failed
    failure_rate = round(failed / executed, 4) if executed else 0.0

    failed_actions = [
        x.get("action")
        for x in results
        if not x.get("success") and x.get("action")
    ]
    repeat_failures = Counter(failed_actions)

    signals = []
    recommendations = []

    if executed == 0:
        signals.append("no_actions_executed")
        recommendations.append("Wait for the next eligible action cycle or refresh the action queue.")

    if failure_rate >= float(cfg.get("failure_rate_threshold", 0.25)):
        signals.append("high_failure_rate")
        recommendations.append("Increase review priority for recently failing internal actions.")

    repeated = [
        action for action, count in repeat_failures.items()
        if count >= int(cfg.get("repeat_failure_threshold", 2))
    ]
    if repeated:
        signals.append("repeated_action_failures")
        recommendations.append(
            "Temporarily lower priority for repeatedly failing actions until the root cause is reviewed."
        )

    if blocked:
        signals.append("actions_blocked_by_eligibility")
        recommendations.append(
            "Keep blocked categories gated until readiness and policy explicitly allow them."
        )

    if not signals:
        signals.append("dispatcher_outcomes_healthy")
        recommendations.append(
            "Current dispatcher outcomes are healthy; preserve current execution policy."
        )

    learning_result = None
    if (
        cfg.get("automatic_learning_trigger", True)
        and ("high_failure_rate" in signals or "repeated_action_failures" in signals)
    ):
        learning_result = run(
            ["python", "companyos/learningctl", "learn"]
        )

    report = {
        "generated_at": now(),
        "executed_actions": executed,
        "successful_actions": succeeded,
        "failed_actions": failed,
        "failure_rate": failure_rate,
        "blocked_actions": len(blocked),
        "signals": signals,
        "repeated_failures": dict(repeat_failures),
        "recommendations": recommendations,
        "learning_triggered": learning_result is not None,
        "learning_result": learning_result,
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
        "last_analyzed_at": now(),
        "executed_actions": executed,
        "successful_actions": succeeded,
        "failed_actions": failed,
        "failure_rate": failure_rate,
        "signal_count": len(signals)
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "failure_rate": failure_rate,
        "signal_count": len(signals)
    })

    return {
        "success": True,
        "status": "dispatcher_feedback_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "dispatcher_feedback_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "analyze":
        result = analyze()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["analyze", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/dispatcher_feedback_loop.py"

cat > "$CTL/dispatcherfeedbackctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "dispatcher_feedback_loop.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/dispatcherfeedbackctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/dispatcher_feedback_loop.py" "$CTL/dispatcherfeedbackctl"

echo "[2/6] Running feedback analysis..."
python "$CTL/dispatcherfeedbackctl" analyze

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "dispatcher-feedback-loop",
    "enabled": True,
    "interval_seconds": 21600,
    "command": ["python", "companyos/dispatcherfeedbackctl", "analyze"]
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

echo "[5/6] Checking feedback status..."
python "$CTL/dispatcherfeedbackctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "dispatcher_feedback_loop.py",
    root / "companyos" / "dispatcherfeedbackctl",
    root / "ceo_memory" / "dispatcher_feedback_config.json",
    root / "ceo_memory" / "dispatcher_feedback_state.json",
    root / "ceo_memory" / "dispatcher_feedback_report.json",
    root / "ceo_memory" / "dispatcher_feedback_health.json",
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

    sched = json.loads(required[6].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "dispatcher-feedback-loop"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Dispatcher feedback scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 6 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 6 INSTALLED"
echo " AUTONOMOUS OUTCOME FEEDBACK LOOP ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/dispatcherfeedbackctl analyze"
echo "  python companyos/dispatcherfeedbackctl status"
