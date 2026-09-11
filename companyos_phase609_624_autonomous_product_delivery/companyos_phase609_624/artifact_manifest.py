import json
from pathlib import Path
from datetime import datetime, timezone

class ArtifactManifest:
    """613: persistent manifest of product-delivery artifacts."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "product_artifacts.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, venture_id, artifacts):
        row = {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "venture_id":venture_id,
            "artifacts":list(artifacts or []),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
