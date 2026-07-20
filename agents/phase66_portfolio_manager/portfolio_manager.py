import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase66"
STATE_FILE = MEMORY / "portfolio.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 66, "projects": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 66, "projects": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def create_project(name, objective, opportunity_id=None):
    data = load()
    project = {
        "project_id": f"proj-{uuid.uuid4().hex[:12]}",
        "opportunity_id": opportunity_id,
        "name": name,
        "objective": objective,
        "status": "planning",
        "health": "unknown",
        "revenue": 0.0,
        "cost": 0.0,
        "created_at": now(),
        "updated_at": now(),
    }
    data.setdefault("projects", []).append(project)
    save(data)
    return {"success": True, "status": "phase66_project_created", "project": project}

def update_project(project_id, **updates):
    data = load()
    allowed = {"status", "health", "revenue", "cost", "objective"}
    for project in data.get("projects", []):
        if project.get("project_id") == project_id:
            for k, v in updates.items():
                if k in allowed:
                    project[k] = v
            project["updated_at"] = now()
            save(data)
            return {"success": True, "status": "phase66_project_updated", "project": project}
    return {"success": False, "status": "phase66_project_not_found", "project_id": project_id}

def status():
    data = load()
    projects = data.get("projects", [])
    return {
        "success": True,
        "status": "phase66_portfolio_status",
        "project_count": len(projects),
        "active_projects": sum(1 for p in projects if p.get("status") not in {"completed", "archived", "failed"}),
        "projects": projects,
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
