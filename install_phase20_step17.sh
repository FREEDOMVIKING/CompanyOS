#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 20 Step 17 - Feedback-to-Priority Learning Integration"
echo "============================================================"

cat > "$MEM/feedback_priority_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_feedback_integration": true,
  "feedback_weight": 0.25,
  "fused_priority_weight": 0.75,
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

cat > "$AGENTS/feedback_priority_integrator.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "feedback_priority_config.json"
FUSED = MEM / "confidence_priority_report.json"
FEEDBACK = MEM / "execution_feedback_report.json"

STATE = MEM / "feedback_priority_state.json"
REPORT = MEM / "feedback_priority_report.json"
HEALTH = MEM / "feedback_priority_health.json"

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

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def integrate() -> dict[str, Any]:
    cfg = load(CFG, {})
    fused = load(FUSED, {}).get("fused_priorities", [])
    feedback_rows = load(FEEDBACK, {}).get("adjustments", [])

    feedback = {
        row.get("action"): row
        for row in feedback_rows
        if row.get("action")
    }

    fw = float(cfg.get("feedback_weight", 0.25))
    pw = float(cfg.get("fused_priority_weight", 0.75))
    total_weight = fw + pw
    if total_weight <= 0:
        fw, pw, total_weight = 0.25, 0.75, 1.0

    low = float(cfg.get("minimum_priority", 1))
    high = float(cfg.get("maximum_priority", 100))

    integrated = []

    for row in fused:
        action = row.get("action")
        if not action:
            continue

        base = float(row.get("fused_priority", 50))
        fb = feedback.get(action, {})
        adjustment = float(fb.get("feedback_adjustment", 0))
        confidence = float(fb.get("confidence", 0))

        adjusted_target = clamp(base + adjustment, low, high)

        final_priority = (
            (base * pw) +
            (adjusted_target * fw)
        ) / total_weight

        final_priority = clamp(final_priority, low, high)

        integrated.append({
            "action": action,
            "base_fused_priority": round(base, 2),
            "feedback_adjustment": round(adjustment, 2),
            "feedback_confidence": round(confidence, 2),
            "final_priority": round(final_priority, 2),
            "reason": row.get("reason"),
            "confidence": row.get("confidence"),
            "learned_score": row.get("learned_score"),
            "adaptive_priority": row.get("adaptive_priority")
        })

    integrated.sort(
        key=lambda x: (
            x["final_priority"],
            x["feedback_confidence"]
        ),
        reverse=True
    )

    report = {
        "generated_at": now(),
        "integrated_priorities": integrated,
        "top_action": integrated[0]["action"] if integrated else None,
        "top_priority": integrated[0]["final_priority"] if integrated else None,
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
        "last_integrated_at": now(),
        "action_count": len(integrated),
        "top_action": report["top_action"],
        "top_priority": report["top_priority"]
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "action_count": len(integrated)
    })

    return {
        "success": True,
        "status": "feedback_priority_integration_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "feedback_priority_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "integrate":
        result = integrate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["integrate", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/feedback_priority_integrator.py"

cat > "$CTL/feedbackpriorityctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "feedback_priority_integrator.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/feedbackpriorityctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/feedback_priority_integrator.py" "$CTL/feedbackpriorityctl"

echo "[2/6] Integrating feedback into priorities..."
python "$CTL/feedbackpriorityctl" integrate

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "feedback-priority-integration",
    "enabled": True,
    "interval_seconds": 21600,
    "command": ["python", "companyos/feedbackpriorityctl", "integrate"]
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

echo "[5/6] Checking integration status..."
python "$CTL/feedbackpriorityctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "feedback_priority_integrator.py",
    root / "companyos" / "feedbackpriorityctl",
    root / "ceo_memory" / "feedback_priority_config.json",
    root / "ceo_memory" / "feedback_priority_state.json",
    root / "ceo_memory" / "feedback_priority_report.json",
    root / "ceo_memory" / "feedback_priority_health.json",
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
    if "integrated_priorities" not in report:
        errors.append("Feedback priority report missing integrated_priorities")

    sched = json.loads(required[6].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "feedback-priority-integration"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Feedback priority scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 17 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 17 INSTALLED"
echo " FEEDBACK-TO-PRIORITY LEARNING INTEGRATION ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/feedbackpriorityctl integrate"
echo "  python companyos/feedbackpriorityctl status"
