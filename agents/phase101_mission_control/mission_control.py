import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase101"
STATE_FILE = MEMORY / "missions.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 101, "missions": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 101, "missions": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def create_mission(title, objective, priority=50):
    data = load()
    mission = {
        "mission_id": f"mission-{uuid.uuid4().hex[:12]}",
        "title": title,
        "objective": objective,
        "priority": max(0, min(100, int(priority))),
        "status": "active",
        "created_at": now(),
        "updated_at": now(),
    }
    data.setdefault("missions", []).append(mission)
    save(data)
    return {"success": True, "status": "phase101_mission_created", "mission": mission}

def active():
    data = load()
    missions = [m for m in data.get("missions", []) if m.get("status") == "active"]
    missions.sort(key=lambda x: x.get("priority", 0), reverse=True)
    return {"success": True, "status": "phase101_active_missions", "missions": missions}

def status():
    data = load()
    return {
        "success": True,
        "status": "phase101_mission_control_status",
        "mission_count": len(data.get("missions", [])),
        "active_count": len([m for m in data.get("missions", []) if m.get("status") == "active"]),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
