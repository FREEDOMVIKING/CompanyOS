import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase71"
STATE_FILE = MEMORY / "evidence_store.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 71, "evidence": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 71, "evidence": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def add_evidence(title, summary, source_type="manual", source_ref=None, confidence=50, tags=None):
    data = load()
    item = {
        "evidence_id": f"ev-{uuid.uuid4().hex[:12]}",
        "title": title,
        "summary": summary,
        "source_type": source_type,
        "source_ref": source_ref,
        "confidence": max(0, min(100, int(confidence))),
        "tags": tags or [],
        "created_at": now(),
    }
    data.setdefault("evidence", []).append(item)
    save(data)
    return {"success": True, "status": "phase71_evidence_added", "evidence": item}

def status():
    data = load()
    return {
        "success": True,
        "status": "phase71_evidence_intake_status",
        "evidence_count": len(data.get("evidence", [])),
        "evidence": data.get("evidence", []),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
