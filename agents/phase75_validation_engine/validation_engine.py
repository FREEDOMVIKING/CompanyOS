import json
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def build_validation_plan(title, assumptions=None):
    assumptions = assumptions or [
        "customer has a painful enough problem",
        "customer will pay for the proposed outcome",
        "delivery can be automated economically",
    ]

    tests = []
    for i, assumption in enumerate(assumptions, start=1):
        tests.append({
            "test_id": f"VAL-{i}",
            "assumption": assumption,
            "method": "Collect reversible evidence before external commitment.",
            "success_metric": "Predefined evidence threshold met.",
            "status": "planned",
        })

    return {
        "success": True,
        "status": "phase75_validation_plan_complete",
        "title": title,
        "tests": tests,
        "created_at": now(),
    }

def status():
    return {"success": True, "status": "phase75_validation_engine_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
