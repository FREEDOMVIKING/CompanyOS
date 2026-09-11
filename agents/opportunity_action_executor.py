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

CFG = MEM / "opportunity_executor_config.json"
QUEUE = MEM / "execution_handoff_queue.json"
ELIGIBILITY = MEM / "execution_eligibility_report.json"

STATE = MEM / "opportunity_executor_state.json"
REPORT = MEM / "opportunity_executor_report.json"
HEALTH = MEM / "opportunity_executor_health.json"

ACTION_MAP = {
    "analyze": ["python", "companyos/briefctl", "generate"],
    "prepare": ["python", "companyos/decisionctl", "prepare"]
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

def run(command: list[str]) -> dict[str, Any]:
    try:
        p = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=300
        )
        return {
            "success": p.returncode == 0,
            "return_code": p.returncode,
            "stdout": p.stdout[-3000:],
            "stderr": p.stderr[-1500:]
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def map_action(item: dict[str, Any]) -> list[str] | None:
    action_id = str(item.get("action_id", ""))
    if action_id.endswith("-analyze"):
        return ACTION_MAP["analyze"]
    if action_id.endswith("-prepare"):
        return ACTION_MAP["prepare"]
    return None

def execute() -> dict[str, Any]:
    cfg = load(CFG, {})
    queue = load(QUEUE, {})
    eligibility = load(ELIGIBILITY, {})

    system_ready = eligibility.get("system_ready") is True
    matrix = eligibility.get("eligibility", {})
    allowed_categories = set(cfg.get("allowed_categories", []))
    maximum = int(cfg.get("maximum_actions_per_cycle", 3))

    results = []
    blocked = []

    for item in queue.get("actions", [])[:maximum]:
        category = item.get("category", "internal_read_only")

        if not system_ready:
            blocked.append({
                **item,
                "status": "blocked",
                "reason": "system_not_ready"
            })
            continue

        if category not in allowed_categories:
            blocked.append({
                **item,
                "status": "blocked",
                "reason": "category_not_allowed"
            })
            continue

        if not bool(matrix.get(category, False)):
            blocked.append({
                **item,
                "status": "blocked",
                "reason": "category_not_eligible"
            })
            continue

        command = map_action(item)
        if not command:
            blocked.append({
                **item,
                "status": "blocked",
                "reason": "no_safe_execution_mapping"
            })
            continue

        result = run(command)
        results.append({
            "action_id": item.get("action_id"),
            "title": item.get("title"),
            "category": category,
            "priority": item.get("priority"),
            "status": "success" if result.get("success") else "failed",
            "result": result
        })

    failures = [x for x in results if x.get("status") == "failed"]

    report = {
        "generated_at": now(),
        "system_ready": system_ready,
        "executed_count": len(results),
        "blocked_count": len(blocked),
        "failure_count": len(failures),
        "results": results,
        "blocked": blocked,
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_execution_at": now(),
        "system_ready": system_ready,
        "executed_count": len(results),
        "blocked_count": len(blocked),
        "failure_count": len(failures)
    })
    save(HEALTH, {
        "healthy": len(failures) == 0,
        "last_checked_at": now(),
        "executed_count": len(results),
        "failure_count": len(failures)
    })

    return {
        "success": len(failures) == 0,
        "status": "opportunity_action_execution_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "opportunity_executor_status",
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
