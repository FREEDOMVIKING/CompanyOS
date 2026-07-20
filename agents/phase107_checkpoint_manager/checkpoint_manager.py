import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase107"
STATE_FILE = MEMORY / "checkpoints.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 107, "checkpoints": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 107, "checkpoints": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def checkpoint(name, state):
    data = load()
    item = {"name": name, "state": state, "created_at": now()}
    data.setdefault("checkpoints", []).append(item)
    save(data)
    return {"success": True, "status": "phase107_checkpoint_saved", "checkpoint": item}

def latest(name=None):
    data = load()
    items = data.get("checkpoints", [])
    if name:
        items = [x for x in items if x.get("name") == name]
    item = items[-1] if items else None
    return {"success": item is not None, "status": "phase107_checkpoint_found" if item else "phase107_checkpoint_not_found", "checkpoint": item}

def status():
    data = load()
    return {"success": True, "status": "phase107_checkpoint_manager_status", "checkpoint_count": len(data.get("checkpoints", []))}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
