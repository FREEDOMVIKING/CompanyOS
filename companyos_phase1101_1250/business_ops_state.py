import json
from pathlib import Path

class BusinessOpsState:
    """1101-1110: persistent venture/business operating state."""
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"business_ops_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            data=json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save(self, venture_id, state):
        data=self.load()
        data[str(venture_id)] = state
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return state
