import json
import sys

from agents.phase90_autonomy_control_plane.autonomyctl import dashboard as phase90_dashboard
from agents.phase91_persistent_task_queue.task_queue import status as queue_status
from agents.phase95_artifact_store.artifact_store import status as artifact_status
from agents.phase96_approval_queue.approval_queue import status as approval_status
from agents.phase97_audit_log.audit_log import status as audit_status
from agents.phase98_execution_worker.execution_worker import execute_next
from agents.phase99_end_to_end_orchestrator.orchestrator import run_once

def output(data):
    print(json.dumps(data, indent=2))

def dashboard():
    return {
        "success": True,
        "status": "phase100_companyos_core_dashboard",
        "autonomy": phase90_dashboard(),
        "task_queue": queue_status(),
        "artifacts": artifact_status(),
        "approvals": approval_status(),
        "audit": audit_status(),
    }

def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "dashboard"

    if cmd in {"dashboard", "status"}:
        result = dashboard()
    elif cmd == "run-once":
        result = run_once()
    elif cmd == "execute-next":
        result = execute_next()
    else:
        result = {
            "success": False,
            "status": "unknown_command",
            "available_commands": ["dashboard", "run-once", "execute-next"],
        }

    output(result)
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
