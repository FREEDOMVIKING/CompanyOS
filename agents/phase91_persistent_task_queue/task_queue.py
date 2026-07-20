import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase91"
STATE_FILE = MEMORY / "task_queue.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 91, "tasks": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 91, "tasks": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def enqueue(title, category="review", action_class="reversible_internal", payload=None, depends_on=None):
    data = load()
    task = {
        "task_id": f"q-{uuid.uuid4().hex[:12]}",
        "title": title,
        "category": category,
        "action_class": action_class,
        "payload": payload or {},
        "depends_on": depends_on or [],
        "status": "queued",
        "created_at": now(),
        "updated_at": now(),
    }
    data.setdefault("tasks", []).append(task)
    save(data)
    return {"success": True, "status": "phase91_task_enqueued", "task": task}

def ready_tasks():
    data = load()
    tasks = data.get("tasks", [])
    completed = {t.get("task_id") for t in tasks if t.get("status") == "completed"}
    ready = []
    for task in tasks:
        if task.get("status") != "queued":
            continue
        deps = task.get("depends_on", [])
        if all(dep in completed for dep in deps):
            ready.append(task)
    return {
        "success": True,
        "status": "phase91_ready_tasks",
        "count": len(ready),
        "tasks": ready,
    }

def update_status(task_id, status, result=None):
    data = load()
    for task in data.get("tasks", []):
        if task.get("task_id") == task_id:
            task["status"] = status
            task["updated_at"] = now()
            if result is not None:
                task["result"] = result
            save(data)
            return {"success": True, "status": "phase91_task_updated", "task": task}
    return {"success": False, "status": "phase91_task_not_found", "task_id": task_id}

def status():
    data = load()
    return {
        "success": True,
        "status": "phase91_task_queue_status",
        "task_count": len(data.get("tasks", [])),
        "tasks": data.get("tasks", []),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
