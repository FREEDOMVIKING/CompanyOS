import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase103"
STATE_FILE = MEMORY / "plans.json"
MEMORY.mkdir(parents=True, exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    if not STATE_FILE.exists():
        return {"phase": 103, "plans": []}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"phase": 103, "plans": []}

def save(data):
    STATE_FILE.write_text(json.dumps(data, indent=2))
    return data

def save_plan(plan):
    data = load()
    plan = dict(plan)
    plan["saved_at"] = now()
    plans = data.setdefault("plans", [])
    mission_id = plan.get("mission_id")
    plans[:] = [p for p in plans if p.get("mission_id") != mission_id]
    plans.append(plan)
    save(data)
    return {"success": True, "status": "phase103_plan_saved", "plan": plan}

def get_plan(mission_id):
    data = load()
    plan = next((p for p in data.get("plans", []) if p.get("mission_id") == mission_id), None)
    return {
        "success": plan is not None,
        "status": "phase103_plan_found" if plan else "phase103_plan_not_found",
        "plan": plan,
    }

def status():
    data = load()
    return {"success": True, "status": "phase103_plan_store_status", "plan_count": len(data.get("plans", []))}

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
