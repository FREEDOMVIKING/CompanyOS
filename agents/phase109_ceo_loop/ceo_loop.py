import json
from datetime import datetime, timezone

from agents.phase108_continuous_mission_runner.mission_runner import seed_active_mission
from agents.phase98_execution_worker.execution_worker import execute_next
from agents.phase91_persistent_task_queue.task_queue import status as queue_status
from agents.phase96_approval_queue.approval_queue import status as approval_status

def now():
    return datetime.now(timezone.utc).isoformat()

def run_cycle(max_tasks=5):
    seed = seed_active_mission()
    results = []

    for _ in range(max(1, int(max_tasks))):
        result = execute_next()
        results.append(result)
        if result.get("status") == "phase98_no_ready_tasks":
            break

    return {
        "success": all(r.get("success", False) for r in results) if results else True,
        "status": "phase109_ceo_loop_cycle_complete",
        "seed": seed,
        "executions": results,
        "queue": queue_status(),
        "approvals": approval_status(),
        "external_action_taken": False,
        "completed_at": now(),
    }

def status():
    return {"success": True, "status": "phase109_ceo_loop_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
