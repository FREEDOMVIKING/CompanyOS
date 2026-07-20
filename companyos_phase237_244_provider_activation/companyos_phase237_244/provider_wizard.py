from __future__ import annotations
import json
from pathlib import Path

class ProviderWizard:
    """237: generate provider-neutral activation files without storing secrets."""

    def __init__(self, project_root):
        self.root = Path(project_root)
        self.runtime = self.root / ".companyos_runtime"
        self.runtime.mkdir(parents=True, exist_ok=True)

    def write_template(self):
        path = self.runtime / "provider_activation_template.json"
        data = {
            "provider": "custom",
            "model": "set-model-name",
            "provider_adapter_command": "set-command-here",
            "coder_command": f"python {self.root}/scripts/companyos_coder_adapter.py",
            "api_key_env": "COMPANYOS_CODER_API_KEY",
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"path": str(path), "config": data}
