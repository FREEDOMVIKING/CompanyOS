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
