import json
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def replan(plan, failed_task_id, failure_reason):
    updated = dict(plan)
    tasks = [dict(t) for t in plan.get("tasks", [])]
    updated["tasks"] = tasks
    updated["replanned_at"] = now()
    updated["replan_reason"] = failure_reason

    for task in tasks:
        if task.get("task_id") == failed_task_id:
            task["status"] = "needs_review"
            task["recovery_note"] = failure_reason
            break

    updated["status"] = "replanned"
    return {
        "success": True,
        "status": "phase105_plan_replanned",
        "plan": updated,
    }

def status():
    return {"success": True, "status": "phase105_replanner_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
