import json
from datetime import datetime, timezone

from agents.phase91_persistent_task_queue.task_queue import enqueue
from agents.phase98_execution_worker.execution_worker import execute_next
from agents.phase96_approval_queue.approval_queue import status as approval_status
from agents.phase95_artifact_store.artifact_store import status as artifact_status

def now():
    return datetime.now(timezone.utc).isoformat()

def run_once(objective="Run one safe autonomous internal business-development step"):
    queued = enqueue(
        title=objective,
        category="research",
        action_class="reversible_internal",
        payload={"objective": objective},
    )
    executed = execute_next()

    return {
        "success": bool(queued.get("success")) and bool(executed.get("success")),
        "status": "phase99_end_to_end_cycle_complete",
        "queued": queued,
        "executed": executed,
        "approvals": approval_status(),
        "artifacts": artifact_status(),
        "external_action_taken": False,
        "completed_at": now(),
    }

def status():
    return {
        "success": True,
        "status": "phase99_end_to_end_orchestrator_status",
        "ready": True,
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
