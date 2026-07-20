from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

class LearningRecorder:
    """266: append improvement outcomes for future autonomous planning."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "improvement_learning.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, proposal, mission, result, verification):
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "proposal": proposal,
            "mission": mission,
            "success": bool(result.get("success")),
            "verification": verification,
            "model_used": (
                result.get("registered", {}).get("model")
                if isinstance(result.get("registered"), dict)
                else None
            ),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
