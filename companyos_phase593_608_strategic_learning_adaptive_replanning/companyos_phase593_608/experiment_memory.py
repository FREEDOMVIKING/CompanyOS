import json
from datetime import datetime, timezone
from pathlib import Path

class ExperimentMemory:
    """599: persistent memory of experiments and outcomes."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "strategic_experiment_memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, venture_id, experiment, outcome):
        row = {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "venture_id":venture_id,
            "experiment":experiment,
            "outcome":outcome,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str)+"\n")
        return row
