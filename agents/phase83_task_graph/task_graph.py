import json
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc).isoformat()

def build_graph(tasks):
    by_id = {t["task_id"]: dict(t) for t in tasks}
    ready, blocked = [], []
    for task in by_id.values():
        deps = task.get("depends_on", [])
        unmet = [d for d in deps if by_id.get(d, {}).get("status") != "completed"]
        task["unmet_dependencies"] = unmet
        if unmet:
            blocked.append(task)
        else:
            ready.append(task)
    return {
        "success": True,
        "status": "phase83_task_graph_built",
        "ready": ready,
        "blocked": blocked,
        "built_at": now(),
    }

def status():
    return {"success": True, "status": "phase83_task_graph_status", "ready": True}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
