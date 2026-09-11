#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "dispatcher_feedback_config.json"
DISPATCH = MEM / "action_dispatcher_report.json"
STATE = MEM / "dispatcher_feedback_state.json"
REPORT = MEM / "dispatcher_feedback_report.json"
HEALTH = MEM / "dispatcher_feedback_health.json"

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
            timeout=300
        )
        return {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-2500:],
            "stderr": proc.stderr[-1200:]
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc)
        }

def analyze() -> dict[str, Any]:
    cfg = load(CFG, {})
    dispatch = load(DISPATCH, {})
    results = dispatch.get("results", [])
    blocked = dispatch.get("blocked", [])

    executed = len(results)
    failed = sum(1 for x in results if not x.get("success"))
    succeeded = executed - failed
    failure_rate = round(failed / executed, 4) if executed else 0.0

    failed_actions = [
        x.get("action")
        for x in results
        if not x.get("success") and x.get("action")
    ]
    repeat_failures = Counter(failed_actions)

    signals = []
    recommendations = []

    if executed == 0:
        signals.append("no_actions_executed")
        recommendations.append("Wait for the next eligible action cycle or refresh the action queue.")

    if failure_rate >= float(cfg.get("failure_rate_threshold", 0.25)):
        signals.append("high_failure_rate")
        recommendations.append("Increase review priority for recently failing internal actions.")

    repeated = [
        action for action, count in repeat_failures.items()
        if count >= int(cfg.get("repeat_failure_threshold", 2))
    ]
    if repeated:
        signals.append("repeated_action_failures")
        recommendations.append(
            "Temporarily lower priority for repeatedly failing actions until the root cause is reviewed."
        )

    if blocked:
        signals.append("actions_blocked_by_eligibility")
        recommendations.append(
            "Keep blocked categories gated until readiness and policy explicitly allow them."
        )

    if not signals:
        signals.append("dispatcher_outcomes_healthy")
        recommendations.append(
            "Current dispatcher outcomes are healthy; preserve current execution policy."
        )

    learning_result = None
    if (
        cfg.get("automatic_learning_trigger", True)
        and ("high_failure_rate" in signals or "repeated_action_failures" in signals)
    ):
        learning_result = run(
            ["python", "companyos/learningctl", "learn"]
        )

    report = {
        "generated_at": now(),
        "executed_actions": executed,
        "successful_actions": succeeded,
        "failed_actions": failed,
        "failure_rate": failure_rate,
        "blocked_actions": len(blocked),
        "signals": signals,
        "repeated_failures": dict(repeat_failures),
        "recommendations": recommendations,
        "learning_triggered": learning_result is not None,
        "learning_result": learning_result,
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
        "last_analyzed_at": now(),
        "executed_actions": executed,
        "successful_actions": succeeded,
        "failed_actions": failed,
        "failure_rate": failure_rate,
        "signal_count": len(signals)
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "failure_rate": failure_rate,
        "signal_count": len(signals)
    })

    return {
        "success": True,
        "status": "dispatcher_feedback_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "dispatcher_feedback_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "analyze":
        result = analyze()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["analyze", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
