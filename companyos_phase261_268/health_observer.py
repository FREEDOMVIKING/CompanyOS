from __future__ import annotations
import json
from pathlib import Path

class HealthObserver:
    """261: collect internal health signals without external side effects."""

    def __init__(self, project_root):
        self.root = Path(project_root)

    def observe(self):
        runtime = self.root / ".companyos_runtime"
        signals = {
            "runtime_dir_exists": runtime.exists(),
            "tests_dir_exists": (self.root / "tests").exists(),
            "git_repo_exists": (self.root / ".git").exists(),
            "capability_registry_exists": (runtime / "capabilities.json").exists(),
            "provider_activation_exists": (runtime / "provider_activation_state.json").exists(),
        }

        capabilities = {}
        cap_file = runtime / "capabilities.json"
        if cap_file.exists():
            try:
                data = json.loads(cap_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    capabilities = data
            except Exception:
                pass

        return {
            "signals": signals,
            "capability_count": len(capabilities),
            "capabilities": capabilities,
        }
