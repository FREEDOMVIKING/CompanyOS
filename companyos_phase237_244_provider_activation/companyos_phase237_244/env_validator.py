from __future__ import annotations
import os
from pathlib import Path

class EnvironmentValidator:
    """238: validate runtime/model connection prerequisites."""

    def validate(self, project_root):
        root = Path(project_root)
        checks = {
            "project_exists": root.exists(),
            "coder_adapter_exists": (root / "scripts" / "companyos_coder_adapter.py").exists(),
            "coder_cmd_set": bool(os.environ.get("COMPANYOS_CODER_CMD", "").strip()),
            "provider_adapter_cmd_set": bool(os.environ.get("COMPANYOS_PROVIDER_ADAPTER_CMD", "").strip()),
        }
        return {
            "checks": checks,
            "ready_for_real_model_probe": all(checks.values()),
            "missing": [k for k,v in checks.items() if not v],
        }
