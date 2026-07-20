#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

PLANS = ROOT / "ceo_memory/phase51/execution_plans.json"
QUEUE = ROOT / "ceo_memory/phase51/task_queue.json"
STATE = ROOT / "ceo_memory/phase51/dispatcher_state.json"


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


def dependencies_complete(task, tasks):
    task_map = {
        item.get("task_id"): item
        for item in tasks
    }

    for dependency in task.get("depends_on", []):
        dep = task_map.get(dependency)

        if not dep:
            return False

        if dep.get("status") != "completed":
            return False

    return True


def dispatch_ready_tasks():
    plans_data = load_json(PLANS, {"plans": []})
    queue_data = load_json(QUEUE, {"tasks": []})

    queued_ids = {
        item.get("task_id")
        for item in queue_data.get("tasks", [])
    }

    dispatched = []
    blocked = []
    approval_required = []

    for plan in plans_data.get("plans", []):

        tasks = plan.get("tasks", [])

        for task in tasks:

            if task.get("status") != "pending":
                continue

            task_id = task.get("task_id")

            if task_id in queued_ids:
                continue

            if not dependencies_complete(task, tasks):
                blocked.append({
                    "task_id": task_id,
                    "reason": "dependencies_incomplete"
                })
                continue

            if task.get("action_class") == "approval_boundary":
                approval_required.append({
                    "task_id": task_id,
                    "plan_id": plan.get("plan_id"),
                    "title": task.get("title"),
                    "reason": "owner_approval_required"
                })
                continue

            queue_item = {
                "task_id": task_id,
                "plan_id": plan.get("plan_id"),
                "opportunity_id": plan.get("opportunity_id"),
                "title": task.get("title"),
                "specialist_role": task.get("specialist_role"),
                "action_class": task.get("action_class"),
                "status": "queued",
                "queued_at": now()
            }

            queue_data.setdefault("tasks", []).append(queue_item)

            task["status"] = "queued"

            queued_ids.add(task_id)
            dispatched.append(queue_item)

    save_json(PLANS, plans_data)
    save_json(QUEUE, queue_data)

    state = {
        "last_run_at": now(),
        "dispatched": len(dispatched),
        "blocked_by_dependencies": len(blocked),
        "approval_required": len(approval_required),
        "total_queued": len(queue_data.get("tasks", []))
    }

    save_json(STATE, state)

    return {
        "success": True,
        "status": "phase51_dispatch_complete",
        "state": state,
        "dispatched_tasks": dispatched,
        "blocked_tasks": blocked,
        "approval_required": approval_required
    }


def status():
    return {
        "success": True,
        "status": "phase51_dispatcher_status",
        "state": load_json(
            STATE,
            {
                "last_run_at": None,
                "dispatched": 0,
                "blocked_by_dependencies": 0,
                "approval_required": 0,
                "total_queued": 0
            }
        ),
        "queue": load_json(QUEUE, {"tasks": []})
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
