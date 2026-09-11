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

CONFIG = MEMORY / "autonomous_health_config.json"
STATE = MEMORY / "autonomous_health_state.json"
REPORT = MEMORY / "autonomous_health_report.json"
AUDIT = MEMORY / "autonomous_health_audit.json"
HALT = MEMORY / "HALT_AUTONOMY"

OPS_STATE = MEMORY / "autonomous_operations_state.json"
OPS_HEALTH = MEMORY / "autonomous_operations_health.json"
WATCHDOG = MEMORY / "watchdog_health.json"
ORCHESTRATOR = MEMORY / "autonomous_orchestrator_health.json"
INTEGRITY = MEMORY / "system_integrity_health.json"
RECOVERY = MEMORY / "exception_recovery_health.json"
LEARNING = MEMORY / "learning_feedback_health.json"
RESOURCE = MEMORY / "resource_workload_health.json"
ACTION = MEMORY / "internal_action_health.json"

COMPONENTS = {
    "operations": OPS_HEALTH,
    "watchdog": WATCHDOG,
    "orchestrator": ORCHESTRATOR,
    "integrity": INTEGRITY,
    "recovery": RECOVERY,
    "learning": LEARNING,
    "resource": RESOURCE,
    "action": ACTION,
}


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


def run(command: list[str], timeout: int = 180) -> dict[str, Any]:
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
            "stdout": proc.stdout[-3000:],
            "stderr": proc.stderr[-1500:],
        }
    except Exception as exc:
        return {
            "success": False,
            "return_code": 1,
            "error": str(exc),
        }


def detect() -> list[dict[str, Any]]:
    config = load_json(CONFIG, {})
    stale_threshold = int(config.get("stale_job_threshold_seconds", 7200))
    issues: list[dict[str, Any]] = []

    for name, path in COMPONENTS.items():
        data = load_json(path, {})
        if not data:
            issues.append({
                "component": name,
                "type": "missing-health",
                "severity": "medium",
            })
            continue

        if data.get("healthy") is False:
            issues.append({
                "component": name,
                "type": "unhealthy",
                "severity": "high",
                "details": data,
            })

    ops_state = load_json(OPS_STATE, {})
    for job_id, state in ops_state.get("jobs", {}).items():
        last_started = state.get("last_started_epoch")
        status = state.get("status")
        if last_started and status == "running":
            age = epoch() - float(last_started)
            if age > stale_threshold:
                issues.append({
                    "component": "scheduler-job",
                    "job_id": job_id,
                    "type": "stalled-job",
                    "severity": "high",
                    "age_seconds": round(age, 2),
                })

        if state.get("last_success") is False and int(state.get("failure_count", 0)) >= 3:
            issues.append({
                "component": "scheduler-job",
                "job_id": job_id,
                "type": "repeated-failure",
                "severity": "high",
                "failure_count": int(state.get("failure_count", 0)),
            })

    return issues


def recover_issue(issue: dict[str, Any]) -> dict[str, Any]:
    component = issue.get("component")
    issue_type = issue.get("type")

    if component == "operations":
        return run([sys.executable, "companyos/operationsctl", "restart"])

    if component == "watchdog":
        return run([sys.executable, "companyos/watchdogctl", "restart"])

    if component == "orchestrator":
        return run([sys.executable, "companyos/orchestratorctl", "run"], 300)

    if component == "integrity":
        return run([sys.executable, "companyos/integrityctl", "check"], 300)

    if component == "recovery":
        return run([sys.executable, "companyos/recoveryctl", "recover"], 300)

    if component == "scheduler-job" and issue_type in {"stalled-job", "repeated-failure"}:
        return run([sys.executable, "companyos/operationsctl", "restart"])

    return {
        "success": False,
        "status": "no_automatic_recovery_mapping",
        "issue": issue,
    }


def supervise() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {"success": False, "status": "health_supervisor_disabled"}
        audit("supervise", result)
        return result

    if HALT.exists():
        result = {
            "success": False,
            "status": "autonomy_halted",
            "halt_file": str(HALT),
        }
        audit("supervise", result)
        return result

    issues = detect()
    recoveries = []
    max_attempts = max(
        0,
        int(config.get("maximum_recovery_attempts_per_cycle", 3)),
    )

    if config.get("automatic_recovery_trigger", True):
        for issue in issues[:max_attempts]:
            recovery = recover_issue(issue)
            recoveries.append({
                "issue": issue,
                "recovery": recovery,
            })

    remaining = detect()

    report = {
        "generated_at": now(),
        "issues_detected": len(issues),
        "recoveries_attempted": len(recoveries),
        "remaining_issues": len(remaining),
        "issues": issues,
        "recoveries": recoveries,
        "remaining": remaining,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False,
    }
    save_json(REPORT, report)

    state = load_json(
        STATE,
        {
            "schema_version": 1,
            "cycle_count": 0,
        },
    )
    state["cycle_count"] = int(state.get("cycle_count", 0)) + 1
    state["last_cycle_at"] = now()
    state["last_issue_count"] = len(issues)
    state["last_remaining_issue_count"] = len(remaining)
    state["last_recovery_count"] = len(recoveries)
    save_json(STATE, state)

    result = {
        "success": len(remaining) == 0,
        "status": (
            "health_supervision_complete"
            if not remaining
            else "health_supervision_attention_required"
        ),
        "report": report,
        "state": state,
    }
    audit("supervise", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "autonomous_health_supervisor_status",
        "config": load_json(CONFIG, {}),
        "state": load_json(STATE, {}),
        "report": load_json(REPORT, {}),
        "halted": HALT.exists(),
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "run":
            return print_result(supervise())
        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_health_action",
            "action": action,
            "allowed": ["run", "status"],
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "autonomous_health_supervisor_error",
            "error": str(exc),
        }
        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
