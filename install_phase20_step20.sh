#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 20 Step 20 - Recovery-Aware Closed Loop Controller"
echo "============================================================"

cat > "$MEM/recovery_closed_loop_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_cycle": true,
  "run_recovery_if_not_ready": true,
  "run_feedback_refresh": true,
  "run_priority_integration": true,
  "run_selection": true,
  "run_plan_build": true,
  "run_guarded_execution": true,
  "run_execution_feedback": true,
  "maximum_execution_actions": 3,
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

cat > "$AGENTS/recovery_closed_loop_controller.py" <<'PY'
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

CFG = MEM / "recovery_closed_loop_config.json"
READINESS = MEM / "readiness2_report.json"

STATE = MEM / "recovery_closed_loop_state.json"
REPORT = MEM / "recovery_closed_loop_report.json"
HEALTH = MEM / "recovery_closed_loop_health.json"

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
            "stdout": p.stdout[-3500:],
            "stderr": p.stderr[-1800:]
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc)
        }

def cycle() -> dict[str, Any]:
    cfg = load(CFG, {})
    steps = []

    readiness_before = load(READINESS, {})
    ready_before = readiness_before.get("decision") == "ready"

    if not ready_before and cfg.get("run_recovery_if_not_ready", True):
        steps.append({
            "step": "readiness_recovery",
            "result": call(["python", "companyos/recovery2ctl", "run"])
        })

    if cfg.get("run_feedback_refresh", True):
        steps.append({
            "step": "execution_feedback",
            "result": call(["python", "companyos/executionfeedbackctl", "analyze"])
        })

    if cfg.get("run_priority_integration", True):
        steps.append({
            "step": "feedback_priority_integration",
            "result": call(["python", "companyos/feedbackpriorityctl", "integrate"])
        })

    if cfg.get("run_selection", True):
        steps.append({
            "step": "closed_loop_selection",
            "result": call(["python", "companyos/closedloopctl", "run"])
        })

    if cfg.get("run_plan_build", True):
        steps.append({
            "step": "fused_plan_build",
            "result": call(["python", "companyos/fusedplanctl", "build"])
        })

    if cfg.get("run_guarded_execution", True):
        steps.append({
            "step": "guarded_execution",
            "result": call(["python", "companyos/guardedexecctl", "run"])
        })

    if cfg.get("run_execution_feedback", True):
        steps.append({
            "step": "post_execution_feedback",
            "result": call(["python", "companyos/executionfeedbackctl", "analyze"])
        })

    readiness_after = load(READINESS, {})
    ready_after = readiness_after.get("decision") == "ready"

    failures = [
        x["step"]
        for x in steps
        if not x.get("result", {}).get("success", False)
    ]

    report = {
        "generated_at": now(),
        "ready_before": ready_before,
        "ready_after": ready_after,
        "steps": steps,
        "failure_count": len(failures),
        "failed_steps": failures,
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
        "ready_before": ready_before,
        "ready_after": ready_after,
        "failure_count": len(failures)
    })
    save(HEALTH, {
        "healthy": len(failures) == 0,
        "last_checked_at": now(),
        "ready_after": ready_after,
        "failure_count": len(failures)
    })

    return {
        "success": len(failures) == 0,
        "status": "recovery_aware_closed_loop_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "recovery_aware_closed_loop_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = cycle()
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

chmod +x "$AGENTS/recovery_closed_loop_controller.py"

cat > "$CTL/loopctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "recovery_closed_loop_controller.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/loopctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/recovery_closed_loop_controller.py" "$CTL/loopctl"

echo "[2/6] Running recovery-aware closed loop..."
python "$CTL/loopctl" run || true

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "recovery-aware-closed-loop",
    "enabled": True,
    "interval_seconds": 3600,
    "command": ["python", "companyos/loopctl", "run"]
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

echo "[5/6] Checking controller status..."
python "$CTL/loopctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "recovery_closed_loop_controller.py",
    root / "companyos" / "loopctl",
    root / "ceo_memory" / "recovery_closed_loop_config.json",
    root / "ceo_memory" / "recovery_closed_loop_state.json",
    root / "ceo_memory" / "recovery_closed_loop_report.json",
    root / "ceo_memory" / "recovery_closed_loop_health.json",
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
        (x for x in sched.get("jobs", []) if x.get("id") == "recovery-aware-closed-loop"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Recovery-aware closed-loop scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 20 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 20 INSTALLED"
echo " RECOVERY-AWARE CLOSED LOOP CONTROLLER ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/loopctl run"
echo "  python companyos/loopctl status"
