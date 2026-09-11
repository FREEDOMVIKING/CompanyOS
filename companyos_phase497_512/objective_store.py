import json
from pathlib import Path

class ObjectiveStore:
    """497: durable strategic objectives for the CEO."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "ceo_objectives.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {
                "primary": "discover, validate, build, and grow valuable businesses",
                "constraints": [
                    "prefer evidence over intuition",
                    "validate before large build commitments",
                    "allocate attention to strongest opportunities",
                ],
            }
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save(self, data):
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
