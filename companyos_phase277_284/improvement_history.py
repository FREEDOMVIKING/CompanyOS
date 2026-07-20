from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

class ImprovementHistory:
    """280: append durable supervisor-level cycle history."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "continuous_improvement_history.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, cycle_number, result):
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle_number": int(cycle_number),
            "success": bool(result.get("success")),
            "status": result.get("status"),
            "proposal": result.get("proposal"),
            "verification": result.get("verification"),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
