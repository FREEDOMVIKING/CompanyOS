import json
from datetime import datetime, timezone
from pathlib import Path

class LearningAudit:
    """604: append-only strategic-learning audit."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "strategic_learning_audit.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, venture_id, lessons, strategy, mission):
        row = {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "venture_id":venture_id,
            "lessons":lessons,
            "strategy":strategy,
            "rewritten_mission":mission,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str)+"\n")
        return row
