#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime, timezone

from agents.phase52_specialist_runtime.runtime import (
    run_specialist as phase52_run_specialist
)

from agents.phase52_specialist_runtime.context_bridge import (
    build_context
)

ROOT = Path(__file__).resolve().parents[2]

PLANS = ROOT / "ceo_memory/phase51/execution_plans.json"
QUEUE = ROOT / "ceo_memory/phase51/task_queue.json"
RESULTS = ROOT / "ceo_memory/phase51/task_results.json"
STATE = ROOT / "ceo_memory/phase51/executor_state.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def find_plan_task(plans_data, task_id):
    for plan in plans_data.get("plans", []):
        for task in plan.get("tasks", []):
            if task.get("task_id") == task_id:
                return plan, task
    return None, None


def run_specialist(task):
    role = task.get("specialist_role")
    title = task.get("title")
    plan_id = task.get("plan_id")
    task_id = task.get("task_id")

    context = build_context(
        plan_id=plan_id,
        task_id=task_id
    )

    result = phase52_run_specialist(
        role=role,
        task=title,
        context=context
    )

    return {
        "success": result.get("success", False),
        "specialist_role": role,
        "task_title": title,
        "execution_mode": "phase52_specialist_runtime",
        "phase52_result": result,
        "completed_at": now()
    }


def execute_next():
    queue_data = load_json(QUEUE, {"tasks": []})
    plans_data = load_json(PLANS, {"plans": []})
    results_data = load_json(RESULTS, {"results": []})

    queued = [
        item for item in queue_data.get("tasks", [])
        if item.get("status") == "queued"
    ]

    if not queued:
        return {
            "success": True,
            "status": "phase51_no_queued_tasks",
            "executed": 0
        }

    queue_item = queued[0]

    if queue_item.get("action_class") != "reversible_internal":
        return {
            "success": False,
            "status": "phase51_execution_blocked",
            "reason": "task_not_autonomously_executable",
            "task_id": queue_item.get("task_id")
        }

    task_id = queue_item.get("task_id")
    plan, task = find_plan_task(plans_data, task_id)

    if not task:
        return {
            "success": False,
            "status": "phase51_task_not_found",
            "task_id": task_id
        }

    queue_item["status"] = "running"
    task["status"] = "running"

    result = run_specialist(queue_item)

    if result.get("success"):
        queue_item["status"] = "completed"
        task["status"] = "completed"
        task["completed_at"] = now()
    else:
        queue_item["status"] = "failed"
        task["status"] = "failed"

    record = {
        "task_id": task_id,
        "plan_id": queue_item.get("plan_id"),
        "specialist_role": queue_item.get("specialist_role"),
        "result": result,
        "recorded_at": now()
    }

    results_data.setdefault("results", []).append(record)

    save_json(QUEUE, queue_data)
    save_json(PLANS, plans_data)
    save_json(RESULTS, results_data)

    state = {
        "last_run_at": now(),
        "last_task_id": task_id,
        "last_status": queue_item.get("status"),
        "total_results": len(results_data.get("results", []))
    }

    save_json(STATE, state)

    return {
        "success": True,
        "status": "phase51_task_execution_complete",
        "task_id": task_id,
        "plan_id": queue_item.get("plan_id"),
        "specialist_role": queue_item.get("specialist_role"),
        "task_status": queue_item.get("status"),
        "result": result
    }


def status():
    return {
        "success": True,
        "status": "phase51_executor_status",
        "state": load_json(
            STATE,
            {
                "last_run_at": None,
                "last_task_id": None,
                "last_status": None,
                "total_results": 0
            }
        ),
        "results": load_json(RESULTS, {"results": []})
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
