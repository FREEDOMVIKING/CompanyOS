import json
from datetime import datetime, timezone

from agents.phase69_autonomous_planner.autonomous_planner import build_plan
from agents.phase83_task_graph.task_graph import build_graph
from agents.phase81_delegation_router.delegation_router import route_task

def now():
    return datetime.now(timezone.utc).isoformat()

def run_cycle():
    plan = build_plan()
    tasks = plan.get("tasks", [])
    graph = build_graph(tasks)
    routes = [route_task({
        "task_id": t.get("task_id"),
        "category": "research" if i == 0 else "strategy",
    }) for i, t in enumerate(graph.get("ready", []))]

    return {
        "success": True,
        "status": "phase89_ceo_cycle_complete",
        "plan": plan,
        "task_graph": graph,
        "routes": routes,
        "external_action_taken": False,
        "completed_at": now(),
    }

def status():
    return {"success": True, "status": "phase89_ceo_cycle_engine_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
