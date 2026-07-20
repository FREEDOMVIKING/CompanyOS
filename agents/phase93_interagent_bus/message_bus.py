import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase93"
STATE_FILE = MEMORY / "messages.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 93, "messages": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 93, "messages": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def send(sender, recipient, subject, body, correlation_id=None):
    data = load()
    message = {
        "message_id": f"msg-{uuid.uuid4().hex[:12]}",
        "sender": sender,
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "correlation_id": correlation_id,
        "status": "unread",
        "created_at": now(),
    }
    data.setdefault("messages", []).append(message)
    save(data)
    return {"success": True, "status": "phase93_message_sent", "message": message}

def inbox(recipient):
    data = load()
    messages = [m for m in data.get("messages", []) if m.get("recipient") == recipient]
    return {
        "success": True,
        "status": "phase93_inbox",
        "recipient": recipient,
        "count": len(messages),
        "messages": messages,
    }

def status():
    data = load()
    return {
        "success": True,
        "status": "phase93_interagent_bus_status",
        "message_count": len(data.get("messages", [])),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
