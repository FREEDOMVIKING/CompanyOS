import json
from datetime import datetime, timezone

from agents.phase91_persistent_task_queue.task_queue import ready_tasks, update_status
from agents.phase92_agent_execution_interface.agent_executor import execute_internal
from agents.phase95_artifact_store.artifact_store import create as create_artifact
from agents.phase97_audit_log.audit_log import record as audit_record
from agents.phase96_approval_queue.approval_queue import submit as submit_approval

def now():
    return datetime.now(timezone.utc).isoformat()

def execute_next():
    ready = ready_tasks().get("tasks", [])
    if not ready:
        return {
            "success": True,
            "status": "phase98_no_ready_tasks",
            "executed": 0,
        }

    task = ready[0]

    if task.get("action_class") != "reversible_internal":
        approval = submit_approval(
            title=task.get("title", "Approval required"),
            action_class=task.get("action_class"),
            details={"task_id": task.get("task_id"), "payload": task.get("payload", {})},
        )
        update_status(task.get("task_id"), "awaiting_approval", approval)
        audit_record("task_routed_to_approval", "phase98_execution_worker", {
            "task_id": task.get("task_id"),
            "approval_id": approval.get("request", {}).get("approval_id"),
        })
        return {
            "success": True,
            "status": "phase98_task_awaiting_approval",
            "task_id": task.get("task_id"),
            "approval": approval,
        }

    update_status(task.get("task_id"), "running")
    result = execute_internal(task)

    if result.get("success"):
        artifact = create_artifact(
            kind="task_result",
            title=task.get("title", "Task result"),
            content=result,
            source_task_id=task.get("task_id"),
            tags=[task.get("category", "review")],
        )
        update_status(task.get("task_id"), "completed", result)
        audit_record("task_completed", result.get("role", "unknown"), {
            "task_id": task.get("task_id"),
            "artifact_id": artifact.get("artifact", {}).get("artifact_id"),
        })
        return {
            "success": True,
            "status": "phase98_task_execution_complete",
            "task": task,
            "result": result,
            "artifact": artifact,
            "completed_at": now(),
        }

    update_status(task.get("task_id"), "failed", result)
    audit_record("task_failed", "phase98_execution_worker", {
        "task_id": task.get("task_id"),
        "status": result.get("status"),
    })
    return {
        "success": False,
        "status": "phase98_task_execution_failed",
        "task": task,
        "result": result,
    }

def status():
    return {"success": True, "status": "phase98_execution_worker_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
