import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase97"
LOG_FILE = MEMORY / "audit.jsonl"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def record(event_type, actor, details=None):
    event = {
        "event_type": event_type,
        "actor": actor,
        "details": details or {},
        "recorded_at": now(),
    }
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(event) + "\n")
    return {"success": True, "status": "phase97_audit_recorded", "event": event}

def recent(limit=50):
    if not LOG_FILE.exists():
        events = []
    else:
        lines = LOG_FILE.read_text().splitlines()[-int(limit):]
        events = []
        for line in lines:
            try:
                events.append(json.loads(line))
            except Exception:
                pass
    return {
        "success": True,
        "status": "phase97_audit_recent",
        "event_count": len(events),
        "events": events,
    }

def status():
    return recent(20)

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
