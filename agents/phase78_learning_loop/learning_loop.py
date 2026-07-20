import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase78"
STATE_FILE = MEMORY / "learning_log.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 78, "lessons": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 78, "lessons": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def record_lesson(source, observation, decision, outcome=None):
    data = load()
    lesson = {
        "lesson_id": f"lesson-{uuid.uuid4().hex[:12]}",
        "source": source,
        "observation": observation,
        "decision": decision,
        "outcome": outcome,
        "created_at": now(),
    }
    data.setdefault("lessons", []).append(lesson)
    save(data)
    return {"success": True, "status": "phase78_lesson_recorded", "lesson": lesson}

def status():
    data = load()
    return {
        "success": True,
        "status": "phase78_learning_loop_status",
        "lesson_count": len(data.get("lessons", [])),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
