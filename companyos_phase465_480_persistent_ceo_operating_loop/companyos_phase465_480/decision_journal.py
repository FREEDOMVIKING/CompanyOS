import json
from pathlib import Path
from datetime import datetime, timezone

class DecisionJournal:
    """469: append-only CEO decision and stage journal."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "ceo_decision_journal.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, stage, result):
        row = {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "stage":stage,
            "result":result,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
