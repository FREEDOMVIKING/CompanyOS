import json
from pathlib import Path

class HypothesisStore:
    """594: durable venture hypotheses."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "venture_hypotheses.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def put(self, venture_id, hypotheses):
        data = self.load()
        data[str(venture_id)] = dict(hypotheses or {})
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return data[str(venture_id)]

    def get(self, venture_id):
        return self.load().get(str(venture_id), {})
