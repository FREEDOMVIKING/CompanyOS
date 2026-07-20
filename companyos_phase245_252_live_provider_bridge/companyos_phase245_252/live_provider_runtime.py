from __future__ import annotations
from pathlib import Path
from .provider_profile import ProviderProfile
from .http_provider_adapter import HttpProviderAdapter
from .live_probe import LiveProbe
from .activation_state import ActivationState

class LiveProviderRuntime:
    """252: activate and verify a real provider-neutral coding endpoint."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.profile = ProviderProfile(self.root)
        self.state = ActivationState(self.root)

    def status(self):
        profile = self.profile.load()
        return {
            "success": True,
            "status": "phase252_live_provider_runtime_ready",
            "profile_configured": bool(profile),
            "live_provider_connected": bool(self.state.path.exists()),
            "autonomy_mode": "high",
        }

    def probe(self):
        profile = self.profile.load()
        if not profile:
            return {"success": False, "reason": "provider_profile_missing"}

        adapter = HttpProviderAdapter(
            profile["endpoint"],
            profile["model"],
            profile["api_key_env"],
        )
        result = LiveProbe().run(adapter)
        self.state.write(
            connected=result["success"],
            provider_name=profile["name"],
            details={"file_count": result.get("file_count", 0)},
        )
        return result
