import json
from pathlib import Path

class OperationsMetricsStore:
    """485: persistent operating metrics by venture id."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "operations_metrics_store.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def put(self, venture_id, metrics):
        data = self.load()
        data[str(venture_id)] = dict(metrics or {})
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data[str(venture_id)]

    def get(self, venture_id):
        return self.load().get(str(venture_id), {})
