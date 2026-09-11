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

CFG = MEM / "recovery_closed_loop_config.json"
READINESS = MEM / "readiness2_report.json"

STATE = MEM / "recovery_closed_loop_state.json"
REPORT = MEM / "recovery_closed_loop_report.json"
HEALTH = MEM / "recovery_closed_loop_health.json"

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

def call(args: list[str], timeout: int = 600) -> dict[str, Any]:
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
            "stdout": p.stdout[-3500:],
            "stderr": p.stderr[-1800:]
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc)
        }

def cycle() -> dict[str, Any]:
    cfg = load(CFG, {})
    steps = []

    readiness_before = load(READINESS, {})
    ready_before = readiness_before.get("decision") == "ready"

    if not ready_before and cfg.get("run_recovery_if_not_ready", True):
        steps.append({
            "step": "readiness_recovery",
            "result": call(["python", "companyos/recovery2ctl", "run"])
        })

    if cfg.get("run_feedback_refresh", True):
        steps.append({
            "step": "execution_feedback",
            "result": call(["python", "companyos/executionfeedbackctl", "analyze"])
        })

    if cfg.get("run_priority_integration", True):
        steps.append({
            "step": "feedback_priority_integration",
            "result": call(["python", "companyos/feedbackpriorityctl", "integrate"])
        })

    if cfg.get("run_selection", True):
        steps.append({
            "step": "closed_loop_selection",
            "result": call(["python", "companyos/closedloopctl", "run"])
        })

    if cfg.get("run_plan_build", True):
        steps.append({
            "step": "fused_plan_build",
            "result": call(["python", "companyos/fusedplanctl", "build"])
        })

    if cfg.get("run_guarded_execution", True):
        steps.append({
            "step": "guarded_execution",
            "result": call(["python", "companyos/guardedexecctl", "run"])
        })

    if cfg.get("run_execution_feedback", True):
        steps.append({
            "step": "post_execution_feedback",
            "result": call(["python", "companyos/executionfeedbackctl", "analyze"])
        })

    readiness_after = load(READINESS, {})
    ready_after = readiness_after.get("decision") == "ready"

    failures = [
        x["step"]
        for x in steps
        if not x.get("result", {}).get("success", False)
    ]

    report = {
        "generated_at": now(),
        "ready_before": ready_before,
        "ready_after": ready_after,
        "steps": steps,
        "failure_count": len(failures),
        "failed_steps": failures,
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
        "last_cycle_at": now(),
        "ready_before": ready_before,
        "ready_after": ready_after,
        "failure_count": len(failures)
    })
    save(HEALTH, {
        "healthy": len(failures) == 0,
        "last_checked_at": now(),
        "ready_after": ready_after,
        "failure_count": len(failures)
    })

    return {
        "success": len(failures) == 0,
        "status": "recovery_aware_closed_loop_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "recovery_aware_closed_loop_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = cycle()
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
