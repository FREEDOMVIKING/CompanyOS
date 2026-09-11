import json
from pathlib import Path

class ValidationMetricsStore:
    """484: persistent validation metrics by opportunity/venture key."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "validation_metrics_store.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def put(self, key, metrics):
        data = self.load()
        data[str(key)] = dict(metrics or {})
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data[str(key)]

    def get(self, key):
        return self.load().get(str(key), {})
