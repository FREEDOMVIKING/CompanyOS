#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "internal_action_config.json"
QUEUE = MEMORY / "internal_action_queue.json"
STATE = MEMORY / "internal_action_state.json"
HEALTH = MEMORY / "internal_action_health.json"
AUDIT = MEMORY / "internal_action_audit.json"
HALT = MEMORY / "HALT_AUTONOMY"

GOALS = MEMORY / "goal_strategy_goals.json"
DECISIONS = MEMORY / "ceo_decision_queue.json"
PRIORITIES = MEMORY / "executive_priority_rankings.json"

ACTION_MAP = {
    "priority-rank": ["python", "companyos/priorityctl", "rank"],
    "decision-prepare": ["python", "companyos/decisionctl", "prepare"],
    "execution-plan-prepare": ["python", "companyos/executionplanctl", "prepare"],
    "improvement-analyze": ["python", "companyos/improvementctl", "analyze"],
    "performance-collect": ["python", "companyos/performancectl", "collect"],
    "forecast-run": ["python", "companyos/forecastctl", "forecast"],
    "brief-generate": ["python", "companyos/briefctl", "generate"],
    "goal-generate": ["python", "companyos/goalctl", "generate"],
    "learning-run": ["python", "companyos/learningctl", "learn"],
    "integrity-check": ["python", "companyos/integrityctl", "check"],
    "backup-create": ["python", "companyos/integrityctl", "backup"],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def add_action(queue: list[dict[str, Any]], action: str, reason: str, priority: int) -> None:
    if any(
        item.get("action") == action and item.get("status") == "pending"
        for item in queue
    ):
        return

    queue.append({
        "id": f"{action}-{int(datetime.now().timestamp())}",
        "action": action,
        "reason": reason,
        "priority": priority,
        "status": "pending",
        "created_at": now(),
        "external_action": False,
    })


def generate_queue() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    store = load_json(
        QUEUE,
        {"schema_version": 1, "actions": []},
    )
    queue = store.setdefault("actions", [])

    priorities = load_json(PRIORITIES, {}).get("rankings", {}).get("priorities", [])
    decisions = load_json(DECISIONS, {}).get("decisions", [])
    goals = load_json(GOALS, {}).get("goals", [])

    critical = sum(1 for item in priorities if item.get("priority_band") == "critical")
    pending_decisions = sum(1 for item in decisions if item.get("status") == "pending")
    active_goals = sum(1 for item in goals if item.get("status") == "active")

    add_action(queue, "integrity-check", "Maintain system integrity before autonomous work.", 100)

    if critical:
        add_action(queue, "priority-rank", f"{critical} critical priorities detected.", 95)

    if pending_decisions:
        add_action(queue, "decision-prepare", f"{pending_decisions} decisions pending.", 90)
        add_action(queue, "execution-plan-prepare", "Keep approved decisions translated into internal plans.", 85)

    if active_goals:
        add_action(queue, "performance-collect", f"{active_goals} active goals require measurement.", 80)
        add_action(queue, "forecast-run", "Refresh forecast against current goals.", 75)

    add_action(queue, "improvement-analyze", "Continuously search for internal process improvements.", 70)
    add_action(queue, "learning-run", "Update internal learning feedback.", 65)
    add_action(queue, "goal-generate", "Refresh autonomous goals and strategy.", 60)
    add_action(queue, "brief-generate", "Refresh executive summary.", 55)

    queue.sort(key=lambda x: int(x.get("priority", 0)), reverse=True)

    save_json(
        QUEUE,
        {
            "schema_version": 1,
            "generated_at": now(),
            "actions": queue,
        },
    )

    result = {
        "success": True,
        "status": "internal_action_queue_generated",
        "pending_count": sum(1 for x in queue if x.get("status") == "pending"),
    }
    audit("generate", result)
    return result


def run_action(action_name: str) -> dict[str, Any]:
    config = load_json(CONFIG, {})
    allowed = set(config.get("allowed_actions", []))

    if action_name not in allowed or action_name not in ACTION_MAP:
        return {
            "success": False,
            "status": "action_not_allowed",
            "action": action_name,
        }

    try:
        proc = subprocess.run(
            ACTION_MAP[action_name],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=300,
        )
        return {
            "success": proc.returncode == 0,
            "status": "action_executed",
            "action": action_name,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-2000:],
        }
    except Exception as exc:
        return {
            "success": False,
            "status": "action_execution_error",
            "action": action_name,
            "error": str(exc),
        }


def execute() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {"success": False, "status": "internal_action_engine_disabled"}
        audit("execute", result)
        return result

    if HALT.exists():
        result = {"success": False, "status": "autonomy_halted"}
        audit("execute", result)
        return result

    generate_queue()

    store = load_json(QUEUE, {"actions": []})
    actions = store.get("actions", [])
    maximum = max(1, int(config.get("maximum_actions_per_cycle", 10)))

    selected = [x for x in actions if x.get("status") == "pending"][:maximum]
    results = []

    for item in selected:
        result = run_action(str(item.get("action")))
        item["status"] = "completed" if result.get("success") else "failed"
        item["finished_at"] = now()
        item["result"] = result
        results.append(result)

    save_json(QUEUE, store)

    failures = [x for x in results if not x.get("success")]

    state = {
        "generated_at": now(),
        "actions_run": len(results),
        "failures": len(failures),
        "results": results,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False,
    }
    save_json(STATE, state)

    save_json(
        HEALTH,
        {
            "healthy": len(failures) == 0,
            "last_execution_at": now(),
            "actions_run": len(results),
            "failure_count": len(failures),
            "last_error": failures[0].get("status") if failures else None,
        },
    )

    result = {
        "success": len(failures) == 0,
        "status": "internal_action_cycle_complete",
        "actions_run": len(results),
        "failures": len(failures),
        "results": results,
    }
    audit("execute", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "internal_action_status",
        "config": load_json(CONFIG, {}),
        "state": load_json(STATE, {}),
        "health": load_json(HEALTH, {}),
    }
    audit("status", result)
    return result


def show_queue() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "internal_action_queue",
        "queue": load_json(QUEUE, {}),
    }
    audit("queue", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "generate":
            return print_result(generate_queue())
        if action == "execute":
            return print_result(execute())
        if action == "queue":
            return print_result(show_queue())
        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_action_engine_action",
            "action": action,
            "allowed": ["generate", "execute", "queue", "status"],
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "internal_action_engine_error",
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
