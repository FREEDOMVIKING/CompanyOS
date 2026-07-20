from __future__ import annotations
import json
from pathlib import Path

class ImprovementStateStore:
    """285: durable state for persistent autonomous improvement."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "persistent_improvement_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {
                "cycles_completed": 0,
                "last_status": None,
                "paused": False,
                "last_capability": None,
            }
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save(self, state):
        self.path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        return state
