import json
from datetime import datetime, timezone
from pathlib import Path

class ValidationEvidenceRecorder:
    """393: append-only validation evidence log."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "validation_evidence.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, opportunity, experiment, metrics):
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "opportunity": opportunity,
            "experiment": experiment,
            "metrics": metrics,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
