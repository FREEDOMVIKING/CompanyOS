import json
from datetime import datetime, timezone

VALID_STAGES = [
    "discovered",
    "validated",
    "designed",
    "mvp",
    "market_test",
    "launch_ready",
    "operating",
    "scaling",
    "paused",
    "archived",
]

def now():
    return datetime.now(timezone.utc).isoformat()

def next_stage(current_stage):
    if current_stage not in VALID_STAGES:
        return {
            "success": False,
            "status": "phase79_invalid_stage",
            "current_stage": current_stage,
        }

    idx = VALID_STAGES.index(current_stage)
    if current_stage in {"paused", "archived"} or idx >= len(VALID_STAGES) - 3:
        next_value = current_stage
    else:
        next_value = VALID_STAGES[idx + 1]

    return {
        "success": True,
        "status": "phase79_stage_transition_proposed",
        "current_stage": current_stage,
        "next_stage": next_value,
        "automatic_external_action": False,
        "created_at": now(),
    }

def status():
    return {
        "success": True,
        "status": "phase79_venture_lifecycle_status",
        "valid_stages": VALID_STAGES,
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
