import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase67"
STATE_FILE = MEMORY / "execution_policy.json"
MEMORY.mkdir(parents=True, exist_ok=True)

SAFE_AUTONOMOUS = {"reversible_internal"}
APPROVAL_REQUIRED = {"financial_commitment", "irreversible_external"}

def now():
    return datetime.now(timezone.utc).isoformat()

def classify(action_class):
    action_class = str(action_class or "").strip()
    if action_class in SAFE_AUTONOMOUS:
        return {
            "decision": "autonomous_allowed",
            "approval_required": False,
            "action_class": action_class,
        }
    if action_class in APPROVAL_REQUIRED:
        return {
            "decision": "owner_approval_required",
            "approval_required": True,
            "action_class": action_class,
        }
    return {
        "decision": "blocked_unknown_action_class",
        "approval_required": True,
        "action_class": action_class,
    }

def status():
    return {
        "success": True,
        "status": "phase67_execution_policy_status",
        "safe_autonomous": sorted(SAFE_AUTONOMOUS),
        "approval_required": sorted(APPROVAL_REQUIRED),
        "checked_at": now(),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
