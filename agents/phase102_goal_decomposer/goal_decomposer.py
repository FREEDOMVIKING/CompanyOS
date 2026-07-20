import json
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def decompose(mission):
    mid = mission.get("mission_id", "mission")
    objective = mission.get("objective", "")
    tasks = [
        {"task_id": f"{mid}-research", "title": f"Research evidence for: {objective}", "category": "research", "depends_on": []},
        {"task_id": f"{mid}-strategy", "title": f"Define strategy for: {objective}", "category": "strategy", "depends_on": [f"{mid}-research"]},
        {"task_id": f"{mid}-build", "title": f"Design reversible MVP for: {objective}", "category": "build", "depends_on": [f"{mid}-strategy"]},
        {"task_id": f"{mid}-validate", "title": f"Validate assumptions for: {objective}", "category": "growth", "depends_on": [f"{mid}-build"]},
        {"task_id": f"{mid}-review", "title": f"Prepare CEO decision package for: {objective}", "category": "review", "depends_on": [f"{mid}-validate"]},
    ]
    for task in tasks:
        task["action_class"] = "reversible_internal"
        task["status"] = "planned"
    return {
        "success": True,
        "status": "phase102_goal_decomposed",
        "mission_id": mid,
        "tasks": tasks,
        "created_at": now(),
    }

def status():
    return {"success": True, "status": "phase102_goal_decomposer_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
