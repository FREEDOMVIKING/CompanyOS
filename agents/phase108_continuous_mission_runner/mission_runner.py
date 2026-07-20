import json
from datetime import datetime, timezone

from agents.phase101_mission_control.mission_control import active
from agents.phase102_goal_decomposer.goal_decomposer import decompose
from agents.phase103_persistent_plan_store.plan_store import save_plan
from agents.phase91_persistent_task_queue.task_queue import enqueue

def now():
    return datetime.now(timezone.utc).isoformat()

def seed_active_mission():
    missions = active().get("missions", [])
    if not missions:
        return {"success": True, "status": "phase108_no_active_missions", "seeded": 0}

    mission = missions[0]
    plan = decompose(mission)
    save_plan(plan)

    seeded = []
    for task in plan.get("tasks", []):
        result = enqueue(
            title=task.get("title"),
            category=task.get("category"),
            action_class=task.get("action_class"),
            payload={"mission_id": mission.get("mission_id")},
            depends_on=[],
        )
        seeded.append(result.get("task", {}).get("task_id"))

    return {
        "success": True,
        "status": "phase108_mission_seeded",
        "mission_id": mission.get("mission_id"),
        "seeded": len(seeded),
        "queue_task_ids": seeded,
        "completed_at": now(),
    }

def status():
    return {"success": True, "status": "phase108_continuous_mission_runner_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
