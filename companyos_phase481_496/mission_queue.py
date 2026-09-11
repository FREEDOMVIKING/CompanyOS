import json
from pathlib import Path

class MissionQueue:
    """482: durable CEO mission queue."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "ceo_mission_queue.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def save(self, missions):
        self.path.write_text(json.dumps(missions, indent=2, default=str), encoding="utf-8")
        return missions

    def enqueue(self, mission):
        items = self.load()
        items.append(mission)
        return self.save(items)
