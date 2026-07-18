#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " Phase 20 Step 19 - Readiness Recovery Coordinator"
echo "============================================================"

cat > "$MEM/readiness_recovery_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_recovery": true,
  "max_recovery_passes": 1,
  "run_runtime_hygiene": true,
  "run_health_check": true,
  "run_resource_check": true,
  "run_backup_check": true,
  "run_watchdog_check": true,
  "run_preflight_refresh": true,
  "run_readiness_refresh": true,
  "run_eligibility_refresh": true,
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

cat > "$AGENTS/readiness_recovery_coordinator.py" <<'PY'
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

CFG = MEM / "readiness_recovery_config.json"
READINESS = MEM / "readiness2_report.json"
ELIGIBILITY = MEM / "execution_eligibility_report.json"

STATE = MEM / "readiness_recovery_state.json"
REPORT = MEM / "readiness_recovery_report.json"
HEALTH = MEM / "readiness_recovery_health.json"

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

def call(args: list[str], timeout: int = 300) -> dict[str, Any]:
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
            "stdout": p.stdout[-3000:],
            "stderr": p.stderr[-1500:]
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc)
        }

def run_recovery() -> dict[str, Any]:
    cfg = load(CFG, {})
    before = load(READINESS, {})
    before_ready = before.get("decision") == "ready"

    actions = []

    if not before_ready and cfg.get("automatic_internal_recovery", True):
        if cfg.get("run_runtime_hygiene", True):
            actions.append({
                "action": "runtime_hygiene",
                "result": call(["python", "companyos/runtimehygienectl", "isolate"])
            })

        if cfg.get("run_health_check", True):
            actions.append({
                "action": "health_check",
                "result": call(["python", "companyos/healthctl", "run"])
            })

        if cfg.get("run_resource_check", True):
            actions.append({
                "action": "resource_check",
                "result": call(["python", "companyos/resourcectl", "run"])
            })

        if cfg.get("run_backup_check", True):
            actions.append({
                "action": "state_backup",
                "result": call(["python", "companyos/backupctl", "backup"])
            })

        if cfg.get("run_watchdog_check", True):
            actions.append({
                "action": "watchdog_check",
                "result": call(["python", "companyos/watchdogctl", "run"])
            })

        if cfg.get("run_preflight_refresh", True):
            actions.append({
                "action": "preflight_refresh",
                "result": call(["python", "companyos/preflight2ctl", "run"])
            })

        if cfg.get("run_readiness_refresh", True):
            actions.append({
                "action": "readiness_refresh",
                "result": call(["python", "companyos/readiness2ctl", "run"])
            })

        if cfg.get("run_eligibility_refresh", True):
            actions.append({
                "action": "eligibility_refresh",
                "result": call(["python", "companyos/eligibilityctl", "run"])
            })

    after = load(READINESS, {})
    eligibility = load(ELIGIBILITY, {})

    after_ready = after.get("decision") == "ready"
    system_ready = eligibility.get("system_ready") is True

    failed_actions = [
        x["action"] for x in actions
        if not x.get("result", {}).get("success", False)
    ]

    report = {
        "generated_at": now(),
        "before_ready": before_ready,
        "after_ready": after_ready,
        "system_ready": system_ready,
        "recovery_actions": actions,
        "failed_recovery_actions": failed_actions,
        "recovery_attempted": bool(actions),
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
        "last_run_at": now(),
        "before_ready": before_ready,
        "after_ready": after_ready,
        "system_ready": system_ready,
        "recovery_attempted": bool(actions),
        "failure_count": len(failed_actions)
    })
    save(HEALTH, {
        "healthy": len(failed_actions) == 0,
        "last_checked_at": now(),
        "after_ready": after_ready,
        "system_ready": system_ready,
        "failure_count": len(failed_actions)
    })

    return {
        "success": len(failed_actions) == 0,
        "status": "readiness_recovery_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "readiness_recovery_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = run_recovery()
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

chmod +x "$AGENTS/readiness_recovery_coordinator.py"

cat > "$CTL/recovery2ctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "readiness_recovery_coordinator.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/recovery2ctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/readiness_recovery_coordinator.py" "$CTL/recovery2ctl"

echo "[2/6] Running readiness recovery..."
python "$CTL/recovery2ctl" run || true

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "readiness-recovery-coordinator",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/recovery2ctl", "run"]
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

echo "[5/6] Checking recovery status..."
python "$CTL/recovery2ctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "readiness_recovery_coordinator.py",
    root / "companyos" / "recovery2ctl",
    root / "ceo_memory" / "readiness_recovery_config.json",
    root / "ceo_memory" / "readiness_recovery_state.json",
    root / "ceo_memory" / "readiness_recovery_report.json",
    root / "ceo_memory" / "readiness_recovery_health.json",
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
        (x for x in sched.get("jobs", []) if x.get("id") == "readiness-recovery-coordinator"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Readiness recovery scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 19 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 19 INSTALLED"
echo " READINESS RECOVERY COORDINATOR ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/recovery2ctl run"
echo "  python companyos/recovery2ctl status"
