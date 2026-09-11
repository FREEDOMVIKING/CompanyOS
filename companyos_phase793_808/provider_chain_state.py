import json
from pathlib import Path

class ProviderChainState:
    """800: persistent provider-chain execution state."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "provider_chain_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save(self, mission_id, result):
        data = self.load()
        data[str(mission_id)] = {
            "provider_chain": result.get("provider_chain", []),
            "execution": result.get("execution", []),
            "completion": result.get("completion", {}),
        }
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return data[str(mission_id)]
