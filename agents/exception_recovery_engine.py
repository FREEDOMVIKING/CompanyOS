#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
LOGS = ROOT / "logs"

CONFIG = MEMORY / "exception_recovery_config.json"
STATE = MEMORY / "exception_recovery_state.json"
HEALTH = MEMORY / "exception_recovery_health.json"
AUDIT = MEMORY / "exception_recovery_audit.json"
HALT = MEMORY / "HALT_AUTONOMY"

OPS_STATE = MEMORY / "autonomous_operations_state.json"
OPS_HEALTH = MEMORY / "autonomous_operations_health.json"
WATCHDOG_HEALTH = MEMORY / "watchdog_health.json"
ORCH_HEALTH = MEMORY / "autonomous_orchestrator_health.json"
INTEGRITY_HEALTH = MEMORY / "system_integrity_health.json"

LOG_FILE = LOGS / "exception_recovery.log"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def epoch() -> float:
    return time.time()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    tmp.replace(path)


def log(message: str) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[{now()}] {message}\n")


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT, [])
    if not isinstance(records, list):
        records = []
    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })
    save_json(AUDIT, records[-1000:])


def run(command: list[str], timeout: int = 300) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-2000:],
        }
    except Exception as exc:
        return {
            "success": False,
            "return_code": 1,
            "error": str(exc),
        }


def detect_issues() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    ops_health = load_json(OPS_HEALTH, {})
    watchdog_health = load_json(WATCHDOG_HEALTH, {})
    orch_health = load_json(ORCH_HEALTH, {})
    integrity_health = load_json(INTEGRITY_HEALTH, {})
    ops_state = load_json(OPS_STATE, {})

    if ops_health and ops_health.get("healthy") is False:
        issues.append({
            "id": "autonomous-operations-unhealthy",
            "severity": "high",
            "recovery": "restart-scheduler",
        })

    if watchdog_health and watchdog_health.get("healthy") is False:
        issues.append({
            "id": "watchdog-unhealthy",
            "severity": "high",
            "recovery": "restart-watchdog",
        })

    if orch_health and orch_health.get("healthy") is False:
        issues.append({
            "id": "orchestrator-unhealthy",
            "severity": "medium",
            "recovery": "run-orchestrator",
        })

    if integrity_health and integrity_health.get("healthy") is False:
        issues.append({
            "id": "integrity-unhealthy",
            "severity": "critical",
            "recovery": "integrity-check",
        })

    for job_id, job_state in ops_state.get("jobs", {}).items():
        failures = int(job_state.get("failure_count", 0))
        last_success = job_state.get("last_success")

        if last_success is False and failures > 0:
            issues.append({
                "id": f"job-failure:{job_id}",
                "severity": "medium",
                "recovery": "run-scheduler-cycle",
                "job_id": job_id,
            })

    deduped = {}
    for issue in issues:
        deduped[issue["id"]] = issue

    return list(deduped.values())


def recovery_allowed(state: dict[str, Any], config: dict[str, Any]) -> bool:
    history = [
        float(item)
        for item in state.get("recovery_epochs", [])
        if epoch() - float(item) < 3600
    ]
    state["recovery_epochs"] = history
    maximum = int(config.get("maximum_recoveries_per_hour", 5))
    return len(history) < maximum


def execute_recovery(issue: dict[str, Any]) -> dict[str, Any]:
    recovery = issue.get("recovery")

    if recovery == "restart-scheduler":
        return run([sys.executable, "companyos/operationsctl", "restart"], 120)

    if recovery == "restart-watchdog":
        return run([sys.executable, "companyos/watchdogctl", "restart"], 120)

    if recovery == "run-orchestrator":
        return run([sys.executable, "companyos/orchestratorctl", "run"], 300)

    if recovery == "integrity-check":
        return run([sys.executable, "companyos/integrityctl", "check"], 300)

    if recovery == "run-scheduler-cycle":
        return run([sys.executable, "companyos/operationsctl", "run-once"], 300)

    return {
        "success": False,
        "error": f"Unknown recovery action: {recovery}",
    }


def recover() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {"success": False, "status": "exception_recovery_disabled"}
        audit("recover", result)
        return result

    if HALT.exists():
        result = {
            "success": False,
            "status": "autonomy_halted_no_recovery",
            "halt_file": str(HALT),
        }
        audit("recover", result)
        return result

    issues = detect_issues()

    state = load_json(
        STATE,
        {
            "schema_version": 1,
            "recovery_epochs": [],
            "issue_history": [],
            "recovery_count": 0,
        },
    )

    if not recovery_allowed(state, config):
        result = {
            "success": False,
            "status": "recovery_rate_limit_reached",
            "issues": issues,
        }
        audit("recover", result)
        return result

    if not issues:
        save_json(
            HEALTH,
            {
                "healthy": True,
                "last_checked_at": now(),
                "issue_count": 0,
                "recovery_attempted": False,
                "last_error": None,
            },
        )
        result = {
            "success": True,
            "status": "no_recovery_needed",
            "issues": [],
        }
        audit("recover", result)
        return result

    actions = []

    if config.get("automatic_backup_before_recovery", True):
        backup = run([sys.executable, "companyos/integrityctl", "backup"], 300)
        actions.append({
            "type": "backup",
            "success": backup.get("success", False),
            "result": backup,
        })

    max_retries = max(0, int(config.get("max_retries_per_issue", 2)))
    backoff = max(0, int(config.get("retry_backoff_seconds", 5)))

    unresolved = []

    for issue in issues:
        attempts = []
        resolved = False

        for attempt in range(max_retries + 1):
            result = execute_recovery(issue)
            attempts.append({
                "attempt": attempt + 1,
                "result": result,
            })

            if result.get("success"):
                resolved = True
                break

            if attempt < max_retries and backoff:
                time.sleep(backoff * (attempt + 1))

        actions.append({
            "type": "issue-recovery",
            "issue": issue,
            "resolved": resolved,
            "attempts": attempts,
        })

        if not resolved:
            unresolved.append(issue)

    if config.get("automatic_integrity_recheck", True):
        integrity = run([sys.executable, "companyos/integrityctl", "check"], 300)
        actions.append({
            "type": "post-recovery-integrity-check",
            "success": integrity.get("success", False),
            "result": integrity,
        })

    recovery_epoch = epoch()
    state.setdefault("recovery_epochs", []).append(recovery_epoch)
    state["recovery_count"] = int(state.get("recovery_count", 0)) + 1
    state["last_recovery_at"] = now()
    state["last_issue_count"] = len(issues)
    state["last_unresolved_count"] = len(unresolved)
    state.setdefault("issue_history", []).append({
        "timestamp": now(),
        "issues": issues,
        "unresolved": unresolved,
    })
    state["issue_history"] = state["issue_history"][-200:]
    save_json(STATE, state)

    healthy = len(unresolved) == 0

    save_json(
        HEALTH,
        {
            "healthy": healthy,
            "last_checked_at": now(),
            "issue_count": len(issues),
            "unresolved_count": len(unresolved),
            "recovery_attempted": True,
            "last_error": (
                None if healthy
                else f"{len(unresolved)} issue(s) unresolved"
            ),
        },
    )

    result = {
        "success": healthy,
        "status": (
            "exception_recovery_complete"
            if healthy else "exception_recovery_incomplete"
        ),
        "issues": issues,
        "unresolved": unresolved,
        "actions": actions,
    }
    audit("recover", result)
    return result


def check() -> dict[str, Any]:
    issues = detect_issues()
    result = {
        "success": True,
        "status": "exception_scan_complete",
        "issue_count": len(issues),
        "issues": issues,
    }
    audit("check", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "exception_recovery_status",
        "config": load_json(CONFIG, {}),
        "state": load_json(STATE, {}),
        "health": load_json(HEALTH, {}),
        "halted": HALT.exists(),
        "log": str(LOG_FILE),
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "check":
            return print_result(check())

        if action == "recover":
            return print_result(recover())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_recovery_action",
            "action": action,
            "allowed": ["check", "recover", "status"],
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "exception_recovery_error",
            "error": str(exc),
        }
        save_json(
            HEALTH,
            {
                "healthy": False,
                "last_checked_at": now(),
                "last_error": str(exc),
            },
        )
        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
