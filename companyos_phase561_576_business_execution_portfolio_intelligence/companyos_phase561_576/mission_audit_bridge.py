from pathlib import Path
import json
from datetime import datetime, timezone

class MissionAuditBridge:
    """572: ensure mission-level execution is auditable."""

    def __init__(self, root):
        self.path=Path(root)/".companyos_runtime"/"mission_audit.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, mission_id, mission_type, result):
        row={
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "mission_id":mission_id,
            "mission_type":mission_type,
            "result":result,
        }
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,default=str)+"\n")
        return row
