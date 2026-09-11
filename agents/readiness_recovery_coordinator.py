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
