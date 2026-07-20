import json
from datetime import datetime, timezone

ALLOWED_INTERNAL_TOOLS = {
    "read_memory",
    "write_memory",
    "score_opportunity",
    "build_plan",
    "evaluate_outcome",
    "create_artifact",
}

APPROVAL_TOOLS = {
    "spend_money",
    "sign_contract",
    "publish_external",
    "send_external_message",
}

def now():
    return datetime.now(timezone.utc).isoformat()

def dispatch(tool_name, args=None):
    args = args or {}
    if tool_name in ALLOWED_INTERNAL_TOOLS:
        return {
            "success": True,
            "status": "phase94_tool_dispatch_allowed",
            "tool_name": tool_name,
            "args": args,
            "execution_mode": "internal_reversible",
            "dispatched_at": now(),
        }

    if tool_name in APPROVAL_TOOLS:
        return {
            "success": False,
            "status": "phase94_tool_dispatch_approval_required",
            "tool_name": tool_name,
            "args": args,
            "approval_required": True,
        }

    return {
        "success": False,
        "status": "phase94_tool_dispatch_blocked",
        "tool_name": tool_name,
        "reason": "Unknown or unapproved tool.",
    }

def status():
    return {
        "success": True,
        "status": "phase94_tool_dispatch_status",
        "allowed_internal_tools": sorted(ALLOWED_INTERNAL_TOOLS),
        "approval_tools": sorted(APPROVAL_TOOLS),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
