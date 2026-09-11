import json
from datetime import datetime, timezone
from pathlib import Path

class QualityPortfolioMemory:
    """540: append-only record of candidate routing decisions."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "quality_portfolio_memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, candidate, event):
        row = {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "candidate":candidate,
            "event":event,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
