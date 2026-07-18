#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase20_step14_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 20 Step 14 - Fused Execution Plan Integration"
echo "============================================================"

for f in \
  "$AGENTS/fused_execution_plan.py" \
  "$CTL/fusedplanctl" \
  "$MEM/fused_execution_plan_config.json" \
  "$MEM/fused_execution_plan_state.json" \
  "$MEM/fused_execution_plan_report.json" \
  "$MEM/fused_execution_plan_health.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/fused_execution_plan_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_plan_building": true,
  "maximum_plan_actions": 5,
  "require_current_execution_eligibility": true,
  "preserve_fused_priority_order": true,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false,
  "credential_export": false,
  "private_key_export": false
}
JSON

cat > "$AGENTS/fused_execution_plan.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "fused_execution_plan_config.json"
SELECTED = MEM / "fused_selector_report.json"
ELIGIBILITY = MEM / "execution_eligibility_report.json"

STATE = MEM / "fused_execution_plan_state.json"
REPORT = MEM / "fused_execution_plan_report.json"
HEALTH = MEM / "fused_execution_plan_health.json"

ACTION_MAP = {
    "refresh-priorities": ["python", "companyos/priorityctl", "rank"],
    "refresh-decisions": ["python", "companyos/decisionctl", "prepare"],
    "refresh-forecast": ["python", "companyos/forecastctl", "forecast"],
    "refresh-brief": ["python", "companyos/briefctl", "generate"],
    "refresh-goals": ["python", "companyos/goalctl", "generate"],
    "run-learning": ["python", "companyos/learningctl", "learn"],
    "run-health": ["python", "companyos/healthctl", "run"],
    "run-readiness": ["python", "companyos/readiness2ctl", "run"],
    "run-outcomes": ["python", "companyos/outcomectl", "measure"],
    "github-read": ["python", "companyos/githubreadctl", "repos", "20"]
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

def build() -> dict[str, Any]:
    cfg = load(CFG, {})
    selection = load(SELECTED, {})
    eligibility = load(ELIGIBILITY, {})

    selected = selection.get("selected_actions", [])
    matrix = eligibility.get("eligibility", {})
    system_ready = eligibility.get("system_ready") is True
    maximum = int(cfg.get("maximum_plan_actions", 5))

    plan = []
    rejected = []

    for index, item in enumerate(selected[:maximum], start=1):
        action = item.get("action")
        category = item.get("category")
        command = ACTION_MAP.get(action)

        if not command:
            rejected.append({
                "action": action,
                "reason": "action_not_mapped"
            })
            continue

        if cfg.get("require_current_execution_eligibility", True):
            if not system_ready:
                rejected.append({
                    "action": action,
                    "reason": "system_not_ready",
                    "category": category
                })
                continue

            if not bool(matrix.get(category, False)):
                rejected.append({
                    "action": action,
                    "reason": "category_not_eligible",
                    "category": category
                })
                continue

        plan.append({
            "step": index,
            "action": action,
            "category": category,
            "fused_priority": item.get("fused_priority"),
            "confidence": item.get("confidence"),
            "learned_score": item.get("learned_score"),
            "adaptive_priority": item.get("adaptive_priority"),
            "reason": item.get("reason"),
            "command": command,
            "status": "planned"
        })

    report = {
        "generated_at": now(),
        "system_ready": system_ready,
        "plan": plan,
        "rejected": rejected,
        "planned_count": len(plan),
        "rejected_count": len(rejected),
        "automatic_external_write": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False,
        "credential_export": False,
        "private_key_export": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_built_at": now(),
        "system_ready": system_ready,
        "planned_count": len(plan),
        "rejected_count": len(rejected),
        "top_planned_action": plan[0]["action"] if plan else None
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "planned_count": len(plan),
        "system_ready": system_ready
    })

    return {
        "success": True,
        "status": "fused_execution_plan_built",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "fused_execution_plan_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "build":
        result = build()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["build", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/fused_execution_plan.py"

cat > "$CTL/fusedplanctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "fused_execution_plan.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/fusedplanctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/fused_execution_plan.py" "$CTL/fusedplanctl"

echo "[2/6] Building fused execution plan..."
python "$CTL/fusedplanctl" build

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "fused-execution-plan",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/fusedplanctl", "build"]
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

echo "[5/6] Checking fused plan status..."
python "$CTL/fusedplanctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "fused_execution_plan.py",
    root / "companyos" / "fusedplanctl",
    root / "ceo_memory" / "fused_execution_plan_config.json",
    root / "ceo_memory" / "fused_execution_plan_state.json",
    root / "ceo_memory" / "fused_execution_plan_report.json",
    root / "ceo_memory" / "fused_execution_plan_health.json",
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
        "automatic_destructive_actions",
        "credential_export",
        "private_key_export"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    report = json.loads(required[4].read_text())
    if "plan" not in report:
        errors.append("Fused execution plan report missing plan")

    sched = json.loads(required[6].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "fused-execution-plan"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Fused execution plan scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 14 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 14 INSTALLED"
echo " FUSED EXECUTION PLAN INTEGRATION ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/fusedplanctl build"
echo "  python companyos/fusedplanctl status"
