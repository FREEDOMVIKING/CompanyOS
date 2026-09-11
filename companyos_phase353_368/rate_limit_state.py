from __future__ import annotations
import json
from pathlib import Path

class RateLimitState:
    """361: persist source error/rate-limit state."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "public_source_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save(self, data):
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
