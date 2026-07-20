import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase62"
JOURNAL = MEMORY / "recovery_journal.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not JOURNAL.exists():
        return {"phase": 62, "events": []}
    try:
        return json.loads(JOURNAL.read_text())
    except Exception:
        return {"phase": 62, "events": []}

def record(event_type, details=None):
    data = load()
    event = {
        "event_type": event_type,
        "details": details or {},
        "recorded_at": now(),
    }
    data.setdefault("events", []).append(event)
    data["last_event"] = event
    JOURNAL.write_text(json.dumps(data, indent=2))
    return {
        "success": True,
        "status": "phase62_recovery_event_recorded",
        "event": event,
        "event_count": len(data["events"]),
    }

def status():
    data = load()
    return {
        "success": True,
        "status": "phase62_recovery_journal_status",
        "event_count": len(data.get("events", [])),
        "last_event": data.get("last_event"),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
