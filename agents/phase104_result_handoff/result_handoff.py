import json
from datetime import datetime, timezone

from agents.phase93_interagent_bus.message_bus import send

def now():
    return datetime.now(timezone.utc).isoformat()

def handoff(sender_role, recipient_role, task_id, result):
    summary = result.get("result", {}).get("summary") if isinstance(result, dict) else None
    message = send(
        sender=sender_role,
        recipient=recipient_role,
        subject=f"Handoff for {task_id}",
        body={
            "task_id": task_id,
            "summary": summary,
            "result": result,
        },
        correlation_id=task_id,
    )
    return {
        "success": True,
        "status": "phase104_result_handoff_complete",
        "handoff": message,
        "completed_at": now(),
    }

def status():
    return {"success": True, "status": "phase104_result_handoff_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
