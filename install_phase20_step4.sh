#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase20_step4_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 20 Step 4 - Autonomous Execution Eligibility Gate"
echo "============================================================"

for f in \
  "$AGENTS/execution_eligibility_gate.py" \
  "$CTL/eligibilityctl" \
  "$MEM/execution_eligibility_config.json" \
  "$MEM/execution_eligibility_state.json" \
  "$MEM/execution_eligibility_report.json" \
  "$MEM/execution_eligibility_health.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/execution_eligibility_config.json" <<'JSON'
{
  "enabled": true,
  "require_readiness_coordinator_ready": true,
  "allow_internal_read_only": true,
  "allow_internal_reversible": true,
  "allow_external_read_only": true,
  "allow_external_write": false,
  "allow_customer_contact": false,
  "allow_publication": false,
  "allow_spending": false,
  "allow_destructive_actions": false,
  "allow_credential_export": false,
  "allow_private_key_export": false
}
JSON

cat > "$AGENTS/execution_eligibility_gate.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "execution_eligibility_config.json"
READINESS = MEM / "readiness2_report.json"
STATE = MEM / "execution_eligibility_state.json"
REPORT = MEM / "execution_eligibility_report.json"
HEALTH = MEM / "execution_eligibility_health.json"

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

def evaluate() -> dict[str, Any]:
    cfg = load(CFG, {})
    readiness = load(READINESS, {})

    ready = readiness.get("decision") == "ready"
    matrix = {
        "internal_read_only": ready and bool(cfg.get("allow_internal_read_only", True)),
        "internal_reversible": ready and bool(cfg.get("allow_internal_reversible", True)),
        "external_read_only": ready and bool(cfg.get("allow_external_read_only", True)),
        "external_write": False,
        "customer_contact": False,
        "publication": False,
        "spending": False,
        "destructive_actions": False,
        "credential_export": False,
        "private_key_export": False
    }

    report = {
        "generated_at": now(),
        "readiness_decision": readiness.get("decision"),
        "system_ready": ready,
        "eligibility": matrix,
        "blocked_categories": [k for k, v in matrix.items() if not v],
        "allowed_categories": [k for k, v in matrix.items() if v]
    }

    save(REPORT, report)
    save(STATE, {
        "last_evaluated_at": now(),
        "system_ready": ready,
        "allowed_count": len(report["allowed_categories"]),
        "blocked_count": len(report["blocked_categories"])
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "system_ready": ready
    })

    return {
        "success": True,
        "status": "execution_eligibility_evaluated",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "execution_eligibility_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "run":
        result = evaluate()
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

chmod +x "$AGENTS/execution_eligibility_gate.py"

cat > "$CTL/eligibilityctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "execution_eligibility_gate.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/eligibilityctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/execution_eligibility_gate.py" "$CTL/eligibilityctl"

echo "[2/6] Evaluating execution eligibility..."
python "$CTL/eligibilityctl" run

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "execution-eligibility-gate",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/eligibilityctl", "run"]
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

echo "[5/6] Checking eligibility status..."
python "$CTL/eligibilityctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "execution_eligibility_gate.py",
    root / "companyos" / "eligibilityctl",
    root / "ceo_memory" / "execution_eligibility_config.json",
    root / "ceo_memory" / "execution_eligibility_state.json",
    root / "ceo_memory" / "execution_eligibility_report.json",
    root / "ceo_memory" / "execution_eligibility_health.json",
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
        "allow_external_write",
        "allow_customer_contact",
        "allow_publication",
        "allow_spending",
        "allow_destructive_actions",
        "allow_credential_export",
        "allow_private_key_export"
    ]:
        if cfg.get(key) is not False:
            errors.append(f"{key} must remain disabled")

    sched = json.loads(required[6].read_text())
    job = next(
        (x for x in sched.get("jobs", []) if x.get("id") == "execution-eligibility-gate"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Execution eligibility scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 4 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 4 INSTALLED"
echo " AUTONOMOUS EXECUTION ELIGIBILITY GATE ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/eligibilityctl run"
echo "  python companyos/eligibilityctl status"
