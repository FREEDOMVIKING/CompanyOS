import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase68"
STATE_FILE = MEMORY / "business_memory.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 68, "memories": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 68, "memories": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def remember(category, summary, evidence=None, tags=None):
    data = load()
    item = {
        "memory_id": f"mem-{uuid.uuid4().hex[:12]}",
        "category": category,
        "summary": summary,
        "evidence": evidence or [],
        "tags": tags or [],
        "created_at": now(),
    }
    data.setdefault("memories", []).append(item)
    save(data)
    return {"success": True, "status": "phase68_memory_recorded", "memory": item}

def recent(limit=20):
    data = load()
    return {
        "success": True,
        "status": "phase68_recent_memory",
        "memories": data.get("memories", [])[-int(limit):],
    }

def status():
    data = load()
    return {
        "success": True,
        "status": "phase68_business_memory_status",
        "memory_count": len(data.get("memories", [])),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
