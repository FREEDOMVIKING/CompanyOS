#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 29 - Live Specialist Result Integration Bridge"
echo "============================================================"

cat > "$MEM/live_result_bridge_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_result_integration": true,
  "maximum_results_per_cycle": 20,
  "minimum_confidence": 0.5,
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_fund_transfer": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/live_specialist_result_bridge.py" <<'PY'
#!/usr/bin/env python3
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "live_result_bridge_config.json"
SOURCE = MEM / "specialist_runtime_results.json"
TARGET = MEM / "specialist_work_results.json"

STATE = MEM / "live_result_bridge_state.json"
REPORT = MEM / "live_result_bridge_report.json"
HEALTH = MEM / "live_result_bridge_health.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

def num(value, default=0):
    try:
        return float(value)
    except Exception:
        return float(default)

def integrate():
    cfg = load(CFG, {})
    source_rows = load(SOURCE, {}).get("results", [])
    target_doc = load(TARGET, {"results": []})
    target_rows = target_doc.get("results", [])

    existing = {
        row.get("result_id") or row.get("work_id")
        for row in target_rows
        if row.get("result_id") or row.get("work_id")
    }

    maximum = int(cfg.get("maximum_results_per_cycle", 20))
    minimum = num(cfg.get("minimum_confidence", 0.5), 0.5)

    added = []
    rejected = []

    for row in source_rows:
        if len(added) >= maximum:
            break

        if row.get("status") != "completed":
            continue

        work_id = row.get("work_id")
        result_id = f"{work_id}-result" if work_id else None

        if not work_id or result_id in existing or work_id in existing:
            continue

        actual = row.get("actual_result")
        if not isinstance(actual, dict):
            rejected.append({
                "work_id": work_id,
                "reason": "missing_structured_actual_result"
            })
            continue

        confidence = num(actual.get("confidence", 0), 0)
        if confidence < minimum:
            rejected.append({
                "work_id": work_id,
                "reason": "confidence_below_threshold",
                "confidence": confidence
            })
            continue

        integrated = {
            "result_id": result_id,
            "work_id": work_id,
            "plan_id": row.get("plan_id"),
            "decision_id": row.get("decision_id"),
            "opportunity_id": row.get("opportunity_id"),
            "title": row.get("title"),
            "specialist_role": row.get("specialist_role"),
            "specialist": row.get("specialist"),
            "work_mode": row.get("action_type"),
            "status": "completed",
            "actual_result": {
                "summary": actual.get("summary"),
                "findings": actual.get("findings", []),
                "recommendations": actual.get("recommendations", []),
                "risks": actual.get("risks", []),
                "next_internal_actions": actual.get("next_internal_actions", []),
                "confidence": confidence
            },
            "execution_boundary": "internal_non_destructive_only",
            "completed_at": row.get("completed_at") or now(),
            "integrated_at": now()
        }

        target_rows.append(integrated)
        added.append(integrated)
        existing.add(result_id)

    save(TARGET, {
        "generated_at": now(),
        "result_count": len(target_rows),
        "results": target_rows
    })

    report = {
        "generated_at": now(),
        "added_count": len(added),
        "rejected_count": len(rejected),
        "total_result_count": len(target_rows),
        "added": added,
        "rejected": rejected,
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_fund_transfer": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_integrated_at": now(),
        "added_count": len(added),
        "rejected_count": len(rejected),
        "total_result_count": len(target_rows)
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "total_result_count": len(target_rows)
    })

    return {
        "success": True,
        "status": "live_specialist_result_bridge_complete",
        "report": report
    }

def status():
    return {
        "success": True,
        "status": "live_specialist_result_bridge_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

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
raise SystemExit(0 if result.get("success") else 1)
PY

chmod +x "$AGENTS/live_specialist_result_bridge.py"

cat > "$CTL/liveresultbridgectl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "live_specialist_result_bridge.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/liveresultbridgectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/live_specialist_result_bridge.py" "$CTL/liveresultbridgectl"

echo "[2/6] Integrating live specialist results..."
python "$CTL/liveresultbridgectl" integrate

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "live-specialist-result-bridge",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/liveresultbridgectl", "integrate"]
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

echo "[4/6] Restarting operations scheduler..."
python "$CTL/operationsctl" restart

echo "[5/6] Checking bridge status..."
python "$CTL/liveresultbridgectl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root/"agents"/"live_specialist_result_bridge.py",
    root/"companyos"/"liveresultbridgectl",
    root/"ceo_memory"/"live_result_bridge_config.json",
    root/"ceo_memory"/"live_result_bridge_state.json",
    root/"ceo_memory"/"live_result_bridge_report.json",
    root/"ceo_memory"/"live_result_bridge_health.json",
    root/"ceo_memory"/"specialist_work_results.json",
    root/"ceo_memory"/"autonomous_operations_config.json"
]

for path in required:
    if not path.exists() or path.stat().st_size <= 0:
        errors.append(f"Missing/empty: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(str(exc))

cfg = json.loads(required[2].read_text())

for key in [
    "automatic_external_write",
    "automatic_customer_contact",
    "automatic_publication",
    "automatic_spending",
    "automatic_fund_transfer",
    "automatic_code_changes",
    "automatic_merge",
    "automatic_deploy",
    "automatic_destructive_actions"
]:
    if cfg.get(key) is not False:
        errors.append(f"{key} must remain disabled")

sched = json.loads(required[7].read_text())
job = next(
    (x for x in sched.get("jobs", [])
     if x.get("id") == "live-specialist-result-bridge"),
    None
)

if not job or job.get("enabled") is not True:
    errors.append("Live specialist result bridge scheduler job missing/disabled")

print("--------------------------------------------")
print("Phase 21 Step 29 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 29 INSTALLED"
echo " LIVE SPECIALIST RESULT INTEGRATION BRIDGE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/liveresultbridgectl integrate"
echo "  python companyos/liveresultbridgectl status"
