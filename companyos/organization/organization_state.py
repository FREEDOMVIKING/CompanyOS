import json
from pathlib import Path

class OrganizationState:
    def __init__(self, root):
        self.path = Path(root)/".companyos_runtime"/"self_managing_org_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            d=json.loads(self.path.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
        except Exception:
            return {}

    def save(self, state):
        self.path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        return state
