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

CFG = MEM / "plan_executor_config.json"
PLAN = MEM / "execution_plan2_report.json"
PREFLIGHT = MEM / "preflight2_report.json"
ELIGIBILITY = MEM / "execution_eligibility_report.json"

STATE = MEM / "plan_executor_state.json"
REPORT = MEM / "plan_executor_report.json"
HEALTH = MEM / "plan_executor_health.json"

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

def run(command: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=600
        )
        return {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-2000:]
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc)
        }

def refresh_gates() -> dict[str, Any]:
    preflight = run(["python", "companyos/preflight2ctl", "run"])
    readiness = run(["python", "companyos/readiness2ctl", "run"])
    eligibility = run(["python", "companyos/eligibilityctl", "run"])
    return {
        "preflight": preflight,
        "readiness": readiness,
        "eligibility": eligibility,
        "success": (
            preflight.get("success", False)
            and readiness.get("success", False)
            and eligibility.get("success", False)
        )
    }

def execute() -> dict[str, Any]:
    cfg = load(CFG, {})
    plan_data = load(PLAN, {})
    plan = plan_data.get("plan", [])
    maximum = int(cfg.get("maximum_actions_per_cycle", 5))

    if not cfg.get("enabled", True):
        return {
            "success": False,
            "status": "plan_executor_disabled"
        }

    results = []
    blocked = []
    gate_history = []

    for item in plan[:maximum]:
        gates = refresh_gates() if cfg.get("revalidate_before_each_action", True) else {"success": True}
        gate_history.append({
            "action": item.get("action"),
            "gates": gates
        })

        preflight = load(PREFLIGHT, {})
        eligibility = load(ELIGIBILITY, {})

        preflight_ready = preflight.get("decision") == "ready"
        system_ready = eligibility.get("system_ready") is True
        category = item.get("category")
        category_allowed = bool(
            eligibility.get("eligibility", {}).get(category, False)
        )

        if cfg.get("require_runtime_aware_preflight_ready", True) and not preflight_ready:
            blocked.append({
                "action": item.get("action"),
                "reason": "preflight_not_ready"
            })
            continue

        if cfg.get("require_execution_eligibility", True):
            if not system_ready:
                blocked.append({
                    "action": item.get("action"),
                    "reason": "system_not_ready"
                })
                continue
            if not category_allowed:
                blocked.append({
                    "action": item.get("action"),
                    "reason": "category_not_eligible",
                    "category": category
                })
                continue

        command = item.get("command")
        if not isinstance(command, list) or not command:
            blocked.append({
                "action": item.get("action"),
                "reason": "invalid_or_missing_command"
            })
            continue

        result = run(command)
        results.append({
            "step": item.get("step"),
            "action": item.get("action"),
            "category": category,
            "priority": item.get("priority"),
            "result": result,
            "success": result.get("success", False)
        })

        if not result.get("success") and cfg.get("stop_on_failure", False):
            break

    failures = [x for x in results if not x.get("success")]

    feedback = run(["python", "companyos/dispatcherfeedbackctl", "analyze"])
    reprioritize = run(["python", "companyos/adaptivepriorityctl", "run"])

    report = {
        "generated_at": now(),
        "planned_count": len(plan),
        "executed_count": len(results),
        "blocked_count": len(blocked),
        "failure_count": len(failures),
        "results": results,
        "blocked": blocked,
        "gate_history": gate_history,
        "feedback_result": feedback,
        "reprioritization_result": reprioritize,
        "automatic_external_write": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False,
        "credential_export": False,
        "private_key_export": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_execution_at": now(),
        "planned_count": len(plan),
        "executed_count": len(results),
        "blocked_count": len(blocked),
        "failure_count": len(failures)
    })
    save(HEALTH, {
        "healthy": len(failures) == 0,
        "last_checked_at": now(),
        "failure_count": len(failures),
        "executed_count": len(results)
    })

    return {
        "success": len(failures) == 0,
        "status": "adaptive_plan_execution_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "adaptive_plan_executor_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = execute()
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
