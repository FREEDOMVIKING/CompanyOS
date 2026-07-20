import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase95"
STATE_FILE = MEMORY / "artifacts.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 95, "artifacts": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 95, "artifacts": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def create(kind, title, content, source_task_id=None, tags=None):
    data = load()
    artifact = {
        "artifact_id": f"art-{uuid.uuid4().hex[:12]}",
        "kind": kind,
        "title": title,
        "content": content,
        "source_task_id": source_task_id,
        "tags": tags or [],
        "created_at": now(),
    }
    data.setdefault("artifacts", []).append(artifact)
    save(data)
    return {"success": True, "status": "phase95_artifact_created", "artifact": artifact}

def status():
    data = load()
    return {
        "success": True,
        "status": "phase95_artifact_store_status",
        "artifact_count": len(data.get("artifacts", [])),
        "artifacts": data.get("artifacts", []),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
