import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase65"
STATE_FILE = MEMORY / "opportunity_pipeline.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 65, "opportunities": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 65, "opportunities": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def add_opportunity(title, summary="", source="internal", score=50):
    data = load()
    item = {
        "opportunity_id": f"opp-{uuid.uuid4().hex[:12]}",
        "title": title,
        "summary": summary,
        "source": source,
        "score": max(0, min(100, int(score))),
        "status": "discovered",
        "created_at": now(),
        "updated_at": now(),
    }
    data.setdefault("opportunities", []).append(item)
    save(data)
    return {"success": True, "status": "phase65_opportunity_added", "opportunity": item}

def shortlist(min_score=65, limit=10):
    data = load()
    items = [
        x for x in data.get("opportunities", [])
        if x.get("status") in {"discovered", "shortlisted"}
        and int(x.get("score", 0)) >= int(min_score)
    ]
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    selected = items[: int(limit)]

    selected_ids = {x["opportunity_id"] for x in selected}
    for x in data.get("opportunities", []):
        if x.get("opportunity_id") in selected_ids:
            x["status"] = "shortlisted"
            x["updated_at"] = now()
    save(data)

    return {
        "success": True,
        "status": "phase65_shortlist_complete",
        "count": len(selected),
        "opportunities": selected,
    }

def status():
    data = load()
    return {
        "success": True,
        "status": "phase65_opportunity_pipeline_status",
        "total": len(data.get("opportunities", [])),
        "opportunities": data.get("opportunities", []),
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
