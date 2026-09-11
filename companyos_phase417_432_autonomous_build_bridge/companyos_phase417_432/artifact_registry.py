import json
from pathlib import Path
from datetime import datetime, timezone

class ArtifactRegistry:
    """422: record generated artifacts without executing them."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "artifact_registry.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, venture_id, artifacts):
        row = {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "venture_id":venture_id,
            "artifacts":artifacts,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
