from __future__ import annotations
import os
from pathlib import Path

from .provider_wizard import ProviderWizard
from .env_validator import EnvironmentValidator
from .mission_seed import MissionSeed
from .activation_probe import ActivationProbe
from .handoff_readiness import HandoffReadiness

class ProviderActivationRuntime:
    """244: coordinate provider activation and handoff readiness."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.wizard = ProviderWizard(self.root)
        self.env = EnvironmentValidator()
        self.seed = MissionSeed()
        self.probe = ActivationProbe()
        self.handoff = HandoffReadiness()

    def status(self):
        env = self.env.validate(self.root)
        coder_cmd = os.environ.get("COMPANYOS_CODER_CMD", "").strip()
        return {
            "success": True,
            "status": "phase244_provider_activation_runtime_ready",
            "environment": env,
            "coder_command_configured": bool(coder_cmd),
            "first_real_mission": self.seed.create(),
            "autonomy_mode": "high",
        }
