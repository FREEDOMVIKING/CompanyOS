#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase20_step3_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM" "$BACKUP"

echo "============================================================"
echo " Phase 20 Step 3 - Autonomous Readiness Coordinator"
echo "============================================================"

for f in \
  "$AGENTS/readiness_coordinator.py" \
  "$CTL/readiness2ctl" \
  "$MEM/readiness2_config.json" \
  "$MEM/readiness2_state.json" \
  "$MEM/readiness2_report.json" \
  "$MEM/readiness2_health.json" \
  "$MEM/autonomous_operations_config.json"
do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done

cat > "$MEM/readiness2_config.json" <<'JSON'
{
  "enabled": true,
  "minimum_reliability_score": 70,
  "require_runtime_aware_preflight_ready": true,
  "require_watchdog_healthy": true,
  "require_no_critical_incident": true,
  "require_resource_health": true,
  "require_recent_backup": true,
  "maximum_backup_age_hours": 12,
  "require_integrity_health": true,
  "automatic_external_write": false,
  "automatic_code_changes": false,
  "automatic_merge": false,
  "automatic_deploy": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "automatic_destructive_actions": false
}
JSON

cat > "$AGENTS/readiness_coordinator.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "readiness2_config.json"
STATE = MEM / "readiness2_state.json"
REPORT = MEM / "readiness2_report.json"
HEALTH = MEM / "readiness2_health.json"

PREFLIGHT = MEM / "preflight2_report.json"
RELIABILITY = MEM / "reliability_report.json"
WATCHDOG = MEM / "watchdog_health.json"
INCIDENT = MEM / "incident_escalation_report.json"
RESOURCE = MEM / "resource_monitor_report.json"
BACKUP = MEM / "state_backup_state.json"
INTEGRITY = MEM / "system_integrity_health.json"

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

def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None

def evaluate() -> dict[str, Any]:
    cfg = load(CFG, {})

    preflight = load(PREFLIGHT, {})
    reliability = load(RELIABILITY, {})
    watchdog = load(WATCHDOG, {})
    incident = load(INCIDENT, {})
    resource = load(RESOURCE, {})
    backup = load(BACKUP, {})
    integrity = load(INTEGRITY, {})

    blockers = []
    warnings = []
    checks = []

    preflight_ready = preflight.get("decision") == "ready"
    checks.append({"check": "runtime_aware_preflight", "passed": preflight_ready})
    if cfg.get("require_runtime_aware_preflight_ready", True) and not preflight_ready:
        blockers.append("runtime_aware_preflight_not_ready")

    reliability_score = reliability.get("reliability_score")
    reliability_ok = (
        isinstance(reliability_score, (int, float))
        and reliability_score >= int(cfg.get("minimum_reliability_score", 70))
    )
    checks.append({
        "check": "reliability_score",
        "passed": reliability_ok,
        "value": reliability_score
    })
    if not reliability_ok:
        blockers.append("reliability_score_below_threshold")

    watchdog_ok = watchdog.get("healthy") is True
    checks.append({"check": "watchdog_health", "passed": watchdog_ok})
    if cfg.get("require_watchdog_healthy", True) and not watchdog_ok:
        blockers.append("watchdog_unhealthy")

    critical_incident = incident.get("critical_incident") is True
    checks.append({"check": "critical_incident_absent", "passed": not critical_incident})
    if cfg.get("require_no_critical_incident", True) and critical_incident:
        blockers.append("critical_incident_present")

    resource_status = resource.get("status")
    resource_ok = resource_status in {"healthy", "warning"}
    checks.append({
        "check": "resource_health",
        "passed": resource_ok,
        "value": resource_status
    })
    if cfg.get("require_resource_health", True) and not resource_ok:
        blockers.append("resource_health_critical")
    elif resource_status == "warning":
        warnings.append("resource_health_warning")

    backup_time = parse_time(backup.get("last_backup_at"))
    backup_age_hours = None
    backup_ok = False
    if backup_time:
        backup_age_hours = round(
            (datetime.now(timezone.utc) - backup_time).total_seconds() / 3600,
            2
        )
        backup_ok = backup_age_hours <= float(cfg.get("maximum_backup_age_hours", 12))

    checks.append({
        "check": "recent_backup",
        "passed": backup_ok,
        "age_hours": backup_age_hours
    })
    if cfg.get("require_recent_backup", True) and not backup_ok:
        blockers.append("backup_missing_or_stale")

    integrity_ok = integrity.get("healthy") is True
    checks.append({"check": "integrity_health", "passed": integrity_ok})
    if cfg.get("require_integrity_health", True) and not integrity_ok:
        blockers.append("integrity_unhealthy")

    decision = "ready" if not blockers else "blocked"

    report = {
        "generated_at": now(),
        "decision": decision,
        "blockers": blockers,
        "warnings": warnings,
        "checks": checks,
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
        "last_evaluated_at": now(),
        "decision": decision,
        "blocker_count": len(blockers),
        "warning_count": len(warnings)
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "decision": decision,
        "blocker_count": len(blockers)
    })

    return {
        "success": True,
        "status": "readiness_coordination_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "readiness_coordinator_status",
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

chmod +x "$AGENTS/readiness_coordinator.py"

cat > "$CTL/readiness2ctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "readiness_coordinator.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root
    )
)
PY

chmod +x "$CTL/readiness2ctl"

echo "[1/6] Compiling..."
python -m py_compile "$AGENTS/readiness_coordinator.py" "$CTL/readiness2ctl"

echo "[2/6] Running readiness coordination..."
python "$CTL/readiness2ctl" run

echo "[3/6] Adding scheduler job..."
python - <<'PY'
import json
from pathlib import Path

p = Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d = json.loads(p.read_text())
jobs = d.setdefault("jobs", [])

job = {
    "id": "readiness-coordinator-v2",
    "enabled": True,
    "interval_seconds": 1800,
    "command": ["python", "companyos/readiness2ctl", "run"]
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

echo "[5/6] Checking readiness..."
python "$CTL/readiness2ctl" status

echo "[6/6] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "readiness_coordinator.py",
    root / "companyos" / "readiness2ctl",
    root / "ceo_memory" / "readiness2_config.json",
    root / "ceo_memory" / "readiness2_state.json",
    root / "ceo_memory" / "readiness2_report.json",
    root / "ceo_memory" / "readiness2_health.json",
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
        (x for x in sched.get("jobs", []) if x.get("id") == "readiness-coordinator-v2"),
        None
    )
    if not job or job.get("enabled") is not True:
        errors.append("Readiness coordinator scheduler job missing/disabled")

except Exception as exc:
    errors.append(str(exc))

print("--------------------------------------------")
print("Phase 20 Step 3 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print("ERROR:", error)

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 20 STEP 3 INSTALLED"
echo " AUTONOMOUS READINESS COORDINATOR ACTIVE"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/readiness2ctl run"
echo "  python companyos/readiness2ctl status"
