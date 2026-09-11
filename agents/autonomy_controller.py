#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "autonomy_core_config.json"
STATE = MEM / "autonomy_core_state.json"
REPORT = MEM / "autonomy_core_report.json"
HEALTH = MEM / "autonomy_core_health.json"

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

def call(args: list[str], timeout: int = 900) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=os.environ.copy()
        )
        return {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-5000:],
            "stderr": proc.stderr[-2500:]
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

PIPELINE = [
    ("readiness_recovery", ["python", "companyos/recovery2ctl", "run"]),
    ("opportunity_cycle", ["python", "companyos/opportunitycyclectl", "run"]),
    ("portfolio_allocation", ["python", "companyos/opportunityportfolioctl", "allocate"]),
    ("portfolio_rebalance", ["python", "companyos/portfoliorebalancectl", "rebalance"]),
    ("portfolio_performance", ["python", "companyos/portfolioperformancectl", "evaluate"]),
    ("internal_resources", ["python", "companyos/resourceallocatectl", "allocate"]),
    ("specialist_delegation", ["python", "companyos/specialistdelegatectl", "plan"]),
    ("multiagent_routing", ["python", "companyos/multiagentroutectl", "route"]),
    ("specialist_result_requests", ["python", "companyos/specialistresultctl", "collect"]),
    ("governed_queue", ["python", "companyos/governedqueuectl", "enqueue"]),
    ("governed_worker", ["python", "companyos/governedworkerctl", "run"]),
    ("specialist_bridge", ["python", "companyos/specialistbridgectl", "bridge"]),
    ("live_specialists", ["python", "companyos/livespecialistctl", "run"]),
    ("result_bridge", ["python", "companyos/liveresultbridgectl", "integrate"]),
    ("validated_insights", ["python", "companyos/insightrefreshctl", "refresh"]),
    ("ceo_insight_integration", ["python", "companyos/specialistinsightctl", "integrate"]),
    ("ceo_decision_synthesis", ["python", "companyos/ceoinsightdecisionctl", "synthesize"]),
    ("ceo_governance", ["python", "companyos/ceodecisiongovernctl", "govern"]),
    ("governed_planning", ["python", "companyos/governedplanctl", "plan"]),
    ("ceo_reasoning_bridge", ["python", "agents/ceo_live_reasoning_bridge.py"])
]

def run_cycle() -> dict[str, Any]:
    cfg = load(CFG, {})
    failures_before_stop = int(cfg.get("max_cycle_failures_before_stop", 3))

    steps = []
    failures = []

    for name, cmd in PIPELINE:
        result = call(cmd)
        steps.append({"step": name, "result": result})

        if not result.get("success", False):
            failures.append(name)

        if len(failures) >= failures_before_stop:
            break

    report = {
        "generated_at": now(),
        "steps": steps,
        "failure_count": len(failures),
        "failed_steps": failures,
        "api_key_available": bool(
            os.getenv("OPENROUTER_API_KEY", "").strip()
            or os.getenv("OPENAI_API_KEY", "").strip()
        ),
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_fund_transfer": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_cycle_at": now(),
        "failure_count": len(failures),
        "failed_steps": failures
    })
    save(HEALTH, {
        "healthy": len(failures) == 0,
        "last_checked_at": now(),
        "failure_count": len(failures)
    })

    return {
        "success": len(failures) == 0,
        "status": "autonomous_ai_operations_cycle_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "autonomy_core_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {}),
        "config": load(CFG, {})
    }

action = sys.argv[1] if len(sys.argv) > 1 else "status"

if action == "run":
    result = run_cycle()
elif action == "status":
    result = status()
else:
    result = {
        "success": False,
        "status": "unknown_action",
        "allowed": ["run", "status"]
    }

print(json.dumps(result, indent=2))
raise SystemExit(0 if result.get("success") else 1)
