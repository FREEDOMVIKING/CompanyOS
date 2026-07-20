from __future__ import annotations
import json
from pathlib import Path

class ProviderProfile:
    """245: persist provider endpoint/model metadata without storing secrets."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "live_provider_profile.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, name, endpoint, model, api_key_env="COMPANYOS_CODER_API_KEY"):
        data = {
            "name": str(name),
            "endpoint": str(endpoint),
            "model": str(model),
            "api_key_env": str(api_key_env),
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    def load(self):
        if not self.path.exists():
            return None
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else None
        except Exception:
            return None
