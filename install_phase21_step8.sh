#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 21 Step 8 - Opportunity Outcome Feedback Engine"
echo "============================================================"

cat > "$MEM/opportunity_outcome_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_outcome_analysis": true,
  "minimum_samples_before_learning": 2,
  "success_reward": 5,
  "failure_penalty": 10,
  "blocked_penalty": 1,
  "automatic_external_write": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/opportunity_outcome_feedback.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "opportunity_outcome_config.json"
EXEC = MEM / "opportunity_executor_report.json"

STATE = MEM / "opportunity_outcome_state.json"
REPORT = MEM / "opportunity_outcome_report.json"
HEALTH = MEM / "opportunity_outcome_health.json"
SCORES = MEM / "opportunity_action_scores.json"

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

def analyze() -> dict[str, Any]:
    cfg = load(CFG, {})
    execution = load(EXEC, {})
    store = load(SCORES, {"schema_version": 1, "actions": {}})
    actions = store.setdefault("actions", {})

    success_reward = float(cfg.get("success_reward", 5))
    failure_penalty = float(cfg.get("failure_penalty", 10))
    blocked_penalty = float(cfg.get("blocked_penalty", 1))
    minimum_samples = int(cfg.get("minimum_samples_before_learning", 2))

    updates = []

    for row in execution.get("results", []):
        action_id = row.get("action_id")
        if not action_id:
            continue

        rec = actions.setdefault(action_id, {
            "score": 50.0,
            "successes": 0,
            "failures": 0,
            "blocked": 0,
            "samples": 0
        })

        if row.get("status") == "success":
            rec["score"] = min(100.0, float(rec.get("score", 50)) + success_reward)
            rec["successes"] = int(rec.get("successes", 0)) + 1
            outcome = "success"
        else:
            rec["score"] = max(0.0, float(rec.get("score", 50)) - failure_penalty)
            rec["failures"] = int(rec.get("failures", 0)) + 1
            outcome = "failure"

        rec["samples"] = int(rec.get("samples", 0)) + 1
        rec["last_updated_at"] = now()

        updates.append({
            "action_id": action_id,
            "outcome": outcome,
            "score": round(rec["score"], 2),
            "samples": rec["samples"],
            "learning_active": rec["samples"] >= minimum_samples
        })

    for row in execution.get("blocked", []):
        action_id = row.get("action_id")
        if not action_id:
            continue

        rec = actions.setdefault(action_id, {
            "score": 50.0,
            "successes": 0,
            "failures": 0,
            "blocked": 0,
            "samples": 0
        })

        rec["score"] = max(0.0, float(rec.get("score", 50)) - blocked_penalty)
        rec["blocked"] = int(rec.get("blocked", 0)) + 1
        rec["samples"] = int(rec.get("samples", 0)) + 1
        rec["last_updated_at"] = now()

        updates.append({
            "action_id": action_id,
            "outcome": "blocked",
            "score": round(rec["score"], 2),
            "samples": rec["samples"],
            "learning_active": rec["samples"] >= minimum_samples
        })

    store["generated_at"] = now()
    save(SCORES, store)

    ranked = sorted(
        (
            {
                "action_id": aid,
                "score": round(float(data.get("score", 0)), 2),
                "successes": int(data.get("successes", 0)),
                "failures": int(data.get("failures", 0)),
                "blocked": int(data.get("blocked", 0)),
                "samples": int(data.get("samples", 0)),
                "learning_active": int(data.get("samples", 0)) >= minimum_samples
            }
            for aid, data in actions.items()
        ),
        key=lambda x: (x["score"], x["samples"]),
        reverse=True
    )

    report = {
        "generated_at": now(),
        "updates": updates,
        "ranked_actions": ranked,
        "top_action": ranked[0]["action_id"] if ranked else None,
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_analyzed_at": now(),
        "tracked_action_count": len(actions),
        "update_count": len(updates),
        "top_action": report["top_action"]
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "tracked_action_count": len(actions),
        "update_count": len(updates)
    })

    return {
        "success": True,
        "status": "opportunity_outcome_feedback_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "opportunity_outcome_feedback_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {}),
        "scores": load(SCORES, {})
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

chmod +x "$AGENTS/opportunity_outcome_feedback.py"

cat > "$CTL/opportunityoutcomectl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "opportunity_outcome_feedback.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/opportunityoutcomectl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/opportunity_outcome_feedback.py" "$CTL/opportunityoutcomectl"

echo "[2/6] Analyzing opportunity execution outcomes..."
python "$CTL/opportunityoutcomectl" analyze

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "opportunity-outcome-feedback",
    "enabled": True,
    "interval_seconds": 21600,
    "command": ["python", "companyos/opportunityoutcomectl", "analyze"]
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

echo "[5/6] Checking outcome feedback status..."
python "$CTL/opportunityoutcomectl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home()/"companyos"
errors = []

required = [
    root/"agents"/"opportunity_outcome_feedback.py",
    root/"companyos"/"opportunityoutcomectl",
    root/"ceo_memory"/"opportunity_outcome_config.json",
    root/"ceo_memory"/"opportunity_outcome_state.json",
    root/"ceo_memory"/"opportunity_outcome_report.json",
    root/"ceo_memory"/"opportunity_outcome_health.json",
    root/"ceo_memory"/"opportunity_action_scores.json",
    root/"ceo_memory"/"autonomous_operations_config.json"
]

for p in required:
    if not p.exists() or p.stat().st_size <= 0:
        errors.append(f"Missing/empty: {p}")

for p in required[:2]:
    try:
        py_compile.compile(str(p), doraise=True)
    except Exception as exc:
        errors.append(str(exc))

cfg = json.loads(required[2].read_text())
for key in [
    "automatic_external_write",
    "automatic_customer_contact",
    "automatic_publication",
    "automatic_spending",
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
     if x.get("id") == "opportunity-outcome-feedback"),
    None
)
if not job or job.get("enabled") is not True:
    errors.append("Opportunity outcome feedback scheduler job missing/disabled")

print("--------------------------------------------")
print("Phase 21 Step 8 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 21 STEP 8 INSTALLED"
echo " OPPORTUNITY OUTCOME FEEDBACK ENGINE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/opportunityoutcomectl analyze"
echo "  python companyos/opportunityoutcomectl status"
