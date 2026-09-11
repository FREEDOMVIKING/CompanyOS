#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "execution_plan2_config.json"
SELECTED = MEM / "decision_selector_report.json"
ELIGIBILITY = MEM / "execution_eligibility_report.json"

STATE = MEM / "execution_plan2_state.json"
REPORT = MEM / "execution_plan2_report.json"
HEALTH = MEM / "execution_plan2_health.json"

ACTION_MAP = {
    "refresh-priorities": ["python", "companyos/priorityctl", "rank"],
    "refresh-decisions": ["python", "companyos/decisionctl", "prepare"],
    "refresh-forecast": ["python", "companyos/forecastctl", "forecast"],
    "refresh-brief": ["python", "companyos/briefctl", "generate"],
    "refresh-goals": ["python", "companyos/goalctl", "generate"],
    "run-learning": ["python", "companyos/learningctl", "learn"],
    "run-health": ["python", "companyos/healthctl", "run"],
    "run-readiness": ["python", "companyos/readiness2ctl", "run"],
    "run-outcomes": ["python", "companyos/outcomectl", "measure"],
    "github-read": ["python", "companyos/githubreadctl", "repos", "20"]
}

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

def build() -> dict[str, Any]:
    cfg = load(CFG, {})
    selection = load(SELECTED, {})
    eligibility = load(ELIGIBILITY, {})

    selected = selection.get("selected_actions", [])
    system_ready = eligibility.get("system_ready") is True
    matrix = eligibility.get("eligibility", {})

    maximum = int(cfg.get("maximum_plan_actions", 5))

    plan = []
    rejected = []

    for index, item in enumerate(selected[:maximum], start=1):
        action = item.get("action")
        category = item.get("category")
        command = ACTION_MAP.get(action)

        if not command:
            rejected.append({
                "action": action,
                "reason": "action_not_mapped"
            })
            continue

        if cfg.get("require_selected_action_eligibility", True):
            if not system_ready or not matrix.get(category, False):
                rejected.append({
                    "action": action,
                    "reason": "not_currently_eligible",
                    "category": category
                })
                continue

        plan.append({
            "step": index,
            "action": action,
            "category": category,
            "priority": item.get("adaptive_priority"),
            "reason": item.get("reason"),
            "command": command,
            "status": "planned"
        })

    report = {
        "generated_at": now(),
        "system_ready": system_ready,
        "plan": plan,
        "rejected": rejected,
        "planned_count": len(plan),
        "rejected_count": len(rejected),
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
        "last_built_at": now(),
        "system_ready": system_ready,
        "planned_count": len(plan),
        "rejected_count": len(rejected),
        "top_planned_action": plan[0]["action"] if plan else None
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "planned_count": len(plan),
        "system_ready": system_ready
    })

    return {
        "success": True,
        "status": "adaptive_execution_plan_built",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "adaptive_execution_plan_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "build":
        result = build()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["build", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
