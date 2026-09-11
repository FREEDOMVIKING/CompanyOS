import json
from pathlib import Path

class CEOState:
    """466: persistent CEO operating-loop state."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "ceo_operating_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {
                "cycles_completed":0,
                "current_stage":"opportunity",
                "last_status":None,
                "last_success":None,
                "active_venture_id":None,
            }
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save(self, state):
        self.path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        return state
