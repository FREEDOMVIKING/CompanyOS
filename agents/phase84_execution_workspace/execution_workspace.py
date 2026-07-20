import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase84"
STATE_FILE = MEMORY / "workspaces.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 84, "workspaces": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 84, "workspaces": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def create(objective):
    data = load()
    ws = {
        "workspace_id": f"ws-{uuid.uuid4().hex[:12]}",
        "objective": objective,
        "tasks": [],
        "results": [],
        "status": "active",
        "created_at": now(),
    }
    data.setdefault("workspaces", []).append(ws)
    save(data)
    return {"success": True, "status": "phase84_workspace_created", "workspace": ws}

def status():
    data = load()
    return {
        "success": True,
        "status": "phase84_execution_workspace_status",
        "workspace_count": len(data.get("workspaces", [])),
        "workspaces": data.get("workspaces", []),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
