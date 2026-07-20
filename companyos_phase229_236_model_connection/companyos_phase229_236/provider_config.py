from __future__ import annotations
import json, os
from pathlib import Path

class ProviderConfig:
    """229: persist non-secret provider settings; secrets stay in environment variables."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "coder_provider.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, provider, model, command, api_key_env="COMPANYOS_CODER_API_KEY"):
        data = {
            "provider": str(provider),
            "model": str(model),
            "command": str(command),
            "api_key_env": str(api_key_env),
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    def load(self):
        if not self.path.exists():
            return None
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def secret_available(self, config=None):
        cfg = config or self.load() or {}
        env_name = cfg.get("api_key_env")
        return bool(env_name and os.environ.get(env_name))
