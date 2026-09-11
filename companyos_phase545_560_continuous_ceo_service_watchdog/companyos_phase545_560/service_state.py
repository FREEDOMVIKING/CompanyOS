import json
from pathlib import Path

class ServiceState:
    """546: persistent service state."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "ceo_service_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {
                "ticks":0,
                "consecutive_failures":0,
                "last_status":None,
                "last_tick_at":None,
                "running":False,
            }
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save(self, state):
        self.path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        return state
