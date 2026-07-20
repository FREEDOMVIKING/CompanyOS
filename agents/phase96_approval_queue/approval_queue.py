import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase96"
STATE_FILE = MEMORY / "approval_queue.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 96, "requests": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 96, "requests": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def submit(title, action_class, details=None):
    data = load()
    request = {
        "approval_id": f"apr-{uuid.uuid4().hex[:12]}",
        "title": title,
        "action_class": action_class,
        "details": details or {},
        "status": "pending",
        "created_at": now(),
    }
    data.setdefault("requests", []).append(request)
    save(data)
    return {"success": True, "status": "phase96_approval_submitted", "request": request}

def decide(approval_id, decision, note=None):
    data = load()
    for req in data.get("requests", []):
        if req.get("approval_id") == approval_id:
            if decision not in {"approved", "rejected"}:
                return {"success": False, "status": "phase96_invalid_decision"}
            req["status"] = decision
            req["decision_note"] = note
            req["decided_at"] = now()
            save(data)
            return {"success": True, "status": "phase96_approval_decided", "request": req}
    return {"success": False, "status": "phase96_approval_not_found", "approval_id": approval_id}

def status():
    data = load()
    pending = [r for r in data.get("requests", []) if r.get("status") == "pending"]
    return {
        "success": True,
        "status": "phase96_approval_queue_status",
        "pending_count": len(pending),
        "requests": data.get("requests", []),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
