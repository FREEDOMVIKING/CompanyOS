#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase20_step13_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 20 Step 13 - Fused Decision Selection Integration"
echo "============================================================"

for f in \
  "$AGENTS/fused_decision_selector.py" \
  "$CTL/fusedselectctl" \
  "$MEM/fused_selector_config.json" \
  "$MEM/fused_selector_state.json" \
  "$MEM/fused_selector_report.json" \
  "$MEM/fused_selector_health.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/fused_selector_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_selection": true,
  "maximum_selected_actions": 5,
  "minimum_fused_priority": 50,
  "require_execution_eligibility": true,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/fused_decision_selector.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "fused_selector_config.json"
FUSED = MEM / "confidence_priority_report.json"
ELIGIBILITY = MEM / "execution_eligibility_report.json"
STATE = MEM / "fused_selector_state.json"
REPORT = MEM / "fused_selector_report.json"
HEALTH = MEM / "fused_selector_health.json"

CATEGORY_MAP = {
    "refresh-priorities": "internal_reversible",
    "refresh-decisions": "internal_reversible",
    "refresh-forecast": "internal_read_only",
    "refresh-brief": "internal_read_only",
    "refresh-goals": "internal_reversible",
    "run-learning": "internal_reversible",
    "run-health": "internal_read_only",
    "run-readiness": "internal_read_only",
    "run-outcomes": "internal_read_only",
    "github-read": "external_read_only"
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

def select() -> dict[str, Any]:
    cfg = load(CFG, {})
    fused = load(FUSED, {}).get("fused_priorities", [])
    eligibility_data = load(ELIGIBILITY, {})

    system_ready = eligibility_data.get("system_ready") is True
    matrix = eligibility_data.get("eligibility", {})

    minimum = float(cfg.get("minimum_fused_priority", 50))
    maximum = int(cfg.get("maximum_selected_actions", 5))

    selected = []
    rejected = []

    for item in fused:
        action = item.get("action")
        score = float(item.get("fused_priority", 0))
        category = CATEGORY_MAP.get(action, "internal_read_only")

        if score < minimum:
            rejected.append({
                "action": action,
                "fused_priority": score,
                "category": category,
                "reason": "below_minimum_fused_priority"
            })
            continue

        if cfg.get("require_execution_eligibility", True):
            if not system_ready:
                rejected.append({
                    "action": action,
                    "fused_priority": score,
                    "category": category,
                    "reason": "system_not_ready"
                })
                continue

            if not bool(matrix.get(category, False)):
                rejected.append({
                    "action": action,
                    "fused_priority": score,
                    "category": category,
                    "reason": "category_not_eligible"
                })
                continue

        selected.append({
            "action": action,
            "category": category,
            "fused_priority": round(score, 2),
            "confidence": item.get("confidence"),
            "learned_score": item.get("learned_score"),
            "adaptive_priority": item.get("adaptive_priority"),
            "reason": item.get("reason")
        })

        if len(selected) >= maximum:
            break

    report = {
        "generated_at": now(),
        "system_ready": system_ready,
        "selected_actions": selected,
        "rejected_actions": rejected,
        "selected_count": len(selected),
        "rejected_count": len(rejected),
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
        "last_selected_at": now(),
        "system_ready": system_ready,
        "selected_count": len(selected),
        "rejected_count": len(rejected),
        "top_selected_action": selected[0]["action"] if selected else None
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "selected_count": len(selected),
        "system_ready": system_ready
    })

    return {
        "success": True,
        "status": "fused_decision_selection_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "fused_decision_selector_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "select":
        result = select()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["select", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/fused_decision_selector.py"

cat > "$CTL/fusedselectctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "fused_decision_selector.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/fusedselectctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/fused_decision_selector.py" "$CTL/fusedselectctl"

echo "[2/6] Selecting fused decisions..."
python "$CTL/fusedselectctl" select

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "fused-decision-selector",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/fusedselectctl", "select"]
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

echo "[5/6] Checking selector status..."
python "$CTL/fusedselectctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "fused_decision_selector.py",
    root / "companyos" / "fusedselectctl",
    root / "ceo_memory" / "fused_selector_config.json",
    root / "ceo_memory" / "fused_selector_state.json",
    root / "ceo_memory" / "fused_selector_report.json",
    root / "ceo_memory" / "fused_selector_health.json",
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
    if "selected_actions" not in report:
        errors.append("Fused selector report missing selected_actions")

    sched = json.loads(required[6].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "fused-decision-selector"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Fused decision selector scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 13 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 13 INSTALLED"
echo " FUSED DECISION SELECTION INTEGRATION ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/fusedselectctl select"
echo "  python companyos/fusedselectctl status"
