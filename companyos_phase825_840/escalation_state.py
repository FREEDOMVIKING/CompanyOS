import json
from pathlib import Path

class EscalationState:
    """831: persistent escalation state by mission."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "research_escalation_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def update(self, mission_id, **fields):
        data = self.load()
        state = dict(data.get(str(mission_id), {}))
        state.update(fields)
        data[str(mission_id)] = state
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return state
