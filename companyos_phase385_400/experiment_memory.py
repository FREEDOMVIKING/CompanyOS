import json
from datetime import datetime, timezone
from pathlib import Path

class ExperimentMemory:
    """397: persistent record of validation plans and outcomes."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "validation_memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, payload):
        row = {"timestamp": datetime.now(timezone.utc).isoformat(), **payload}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
