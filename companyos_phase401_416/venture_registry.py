import json
from pathlib import Path

class VentureRegistry:
    """413: durable portfolio registry."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "venture_registry.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def upsert(self, venture_id, record):
        data = self.load()
        data[venture_id] = record
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return data[venture_id]
