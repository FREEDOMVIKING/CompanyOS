from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

class ActivationState:
    """251: persist live provider activation status."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "provider_activation_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, connected, provider_name=None, details=None):
        data = {
            "connected": bool(connected),
            "provider_name": provider_name,
            "details": details or {},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
