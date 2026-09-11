import json
from pathlib import Path

class VentureQueue:
    """434: durable venture execution queue."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "venture_execution_queue.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def save(self, items):
        self.path.write_text(json.dumps(items, indent=2, default=str), encoding="utf-8")
        return items

    def enqueue(self, item):
        items = self.load()
        items.append(item)
        return self.save(items)
