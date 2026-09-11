import json
from pathlib import Path

class StrategyState:
    """596: persistent strategy state per venture."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "venture_strategy_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def put(self, venture_id, state):
        data = self.load()
        data[str(venture_id)] = dict(state or {})
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return data[str(venture_id)]
