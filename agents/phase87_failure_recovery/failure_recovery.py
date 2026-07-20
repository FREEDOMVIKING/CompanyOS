import json
from datetime import datetime, timezone

RECOVERY_ACTIONS = {
    "transient": "retry_with_backoff",
    "dependency": "wait_for_dependency",
    "validation": "return_to_validation",
    "policy": "hold_for_owner_review",
    "unknown": "halt_and_record",
}

def now():
    return datetime.now(timezone.utc).isoformat()

def classify_failure(error_type="unknown", details=None):
    action = RECOVERY_ACTIONS.get(error_type, RECOVERY_ACTIONS["unknown"])
    return {
        "success": True,
        "status": "phase87_recovery_strategy_selected",
        "error_type": error_type,
        "details": details or {},
        "recovery_action": action,
        "autonomous_retry_allowed": action in {"retry_with_backoff", "wait_for_dependency", "return_to_validation"},
        "selected_at": now(),
    }

def status():
    return {
        "success": True,
        "status": "phase87_failure_recovery_status",
        "strategies": RECOVERY_ACTIONS,
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
