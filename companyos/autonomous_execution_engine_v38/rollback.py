from pathlib import Path
from .storage import atomic_write_json, now

def create_snapshot(ws, plan):
    snap = {
        "execution_id": plan["execution_id"],
        "venture_id": plan["venture_id"],
        "workspace": str(ws),
        "snapshot_type": "LOCAL_PRE_EXTERNAL_EXECUTION",
        "external_state_changed": False,
        "created_at": now(),
    }
    atomic_write_json(Path(ws) / "rollback/rollback_snapshot.json", snap)
    return snap
