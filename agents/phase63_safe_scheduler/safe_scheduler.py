import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase63"
STATE_FILE = MEMORY / "scheduler_state.json"
MEMORY.mkdir(parents=True, exist_ok=True)

ALLOWED_ACTION_CLASSES = {"reversible_internal"}
BLOCKED_ACTION_CLASSES = {"financial_commitment", "irreversible_external"}

def now():
    return datetime.now(timezone.utc).isoformat()

def default_state():
    return {
        "phase": 63,
        "enabled": False,
        "interval_seconds": 300,
        "objective": None,
        "action_class": "reversible_internal",
        "last_updated": now(),
    }

def load():
    if not STATE_FILE.exists():
        state = default_state()
        save(state)
        return state
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        state = default_state()
        save(state)
        return state

def save(state):
    state["last_updated"] = now()
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return state

def configure(objective, interval_seconds=300, action_class="reversible_internal"):
    if action_class not in ALLOWED_ACTION_CLASSES:
        return {
            "success": False,
            "status": "phase63_scheduler_action_blocked",
            "reason": "Only reversible_internal scheduling is autonomous.",
            "action_class": action_class,
        }

    state = load()
    state["objective"] = objective
    state["interval_seconds"] = max(30, int(interval_seconds))
    state["action_class"] = action_class
    state["enabled"] = True
    save(state)

    return {
        "success": True,
        "status": "phase63_scheduler_configured",
        "state": state,
    }

def disable():
    state = load()
    state["enabled"] = False
    save(state)
    return {
        "success": True,
        "status": "phase63_scheduler_disabled",
        "state": state,
    }

def status():
    return {
        "success": True,
        "status": "phase63_scheduler_status",
        "state": load(),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
