import json
from datetime import datetime, timezone

from agents.phase65_opportunity_pipeline.opportunity_pipeline import shortlist
from agents.phase67_execution_policy.execution_policy import classify

def now():
    return datetime.now(timezone.utc).isoformat()

def build_plan(min_score=65, limit=5):
    shortlisted = shortlist(min_score=min_score, limit=limit)
    tasks = []

    for idx, opp in enumerate(shortlisted.get("opportunities", []), start=1):
        tasks.append({
            "task_id": f"{opp['opportunity_id']}-T{idx}",
            "opportunity_id": opp["opportunity_id"],
            "title": f"Validate and advance: {opp['title']}",
            "action_class": "reversible_internal",
            "policy": classify("reversible_internal"),
            "status": "planned",
        })

    return {
        "success": True,
        "status": "phase69_autonomous_plan_built",
        "created_at": now(),
        "task_count": len(tasks),
        "tasks": tasks,
    }

def status():
    return {
        "success": True,
        "status": "phase69_autonomous_planner_status",
        "ready": True,
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
