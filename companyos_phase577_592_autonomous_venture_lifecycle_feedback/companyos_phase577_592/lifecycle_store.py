import json
from pathlib import Path

class LifecycleStore:
    """578: durable venture lifecycle records."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "venture_lifecycle_store.json"
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
        current = data.get(venture_id, {})
        current.update(record)
        data[venture_id] = current
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return current

    def get(self, venture_id):
        return self.load().get(venture_id)
