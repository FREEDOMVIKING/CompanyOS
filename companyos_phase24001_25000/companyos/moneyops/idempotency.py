import json
from pathlib import Path

class IdempotencyStore:
    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "financial_idempotency.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, data):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        tmp.replace(self.path)

    def get(self, key):
        return self._load().get(str(key))

    def put(self, key, value):
        data = self._load()
        data[str(key)] = value
        self._save(data)
        return value
