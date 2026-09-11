from __future__ import annotations
import json
from pathlib import Path

class ValidationQueue:
    """313: durable queue of top opportunities awaiting validation."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "validation_queue.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, ranked):
        payload = [x for x in ranked if x.get("valid")]
        self.path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return payload

    def load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []
