import json
from datetime import datetime, timezone

from agents.phase81_delegation_router.delegation_router import route_task
from agents.phase82_specialist_registry.specialist_registry import get as get_specialist

def now():
    return datetime.now(timezone.utc).isoformat()

def execute_internal(task):
    route = route_task(task)
    role = route.get("assigned_role")
    specialist = get_specialist(role)

    if task.get("action_class") != "reversible_internal":
        return {
            "success": False,
            "status": "phase92_execution_blocked",
            "reason": "Only reversible_internal tasks can execute autonomously.",
            "task_id": task.get("task_id"),
            "action_class": task.get("action_class"),
        }

    result = {
        "summary": f"{role} processed task: {task.get('title')}",
        "role": role,
        "capabilities": specialist.get("capabilities", []),
        "payload_received": task.get("payload", {}),
    }

    return {
        "success": True,
        "status": "phase92_internal_task_executed",
        "task_id": task.get("task_id"),
        "role": role,
        "result": result,
        "completed_at": now(),
    }

def status():
    return {"success": True, "status": "phase92_agent_execution_interface_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
