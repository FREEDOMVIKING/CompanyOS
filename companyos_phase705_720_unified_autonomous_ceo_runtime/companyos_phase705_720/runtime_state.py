import json
from pathlib import Path

class RuntimeState:
    """705: persistent unified CEO runtime state."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "unified_ceo_runtime_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {
                "cycles":0,
                "last_status":None,
                "last_venture_id":None,
                "last_mission_id":None,
                "consecutive_failures":0,
                "safe_mode":False,
            }
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save(self, state):
        self.path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        return state
