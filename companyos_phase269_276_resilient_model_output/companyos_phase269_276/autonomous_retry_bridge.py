from __future__ import annotations
from pathlib import Path

from companyos_phase253_260 import BuilderBridge
from .resilient_openrouter_adapter import ResilientOpenRouterAdapter

class AutonomousRetryBridge:
    """275: use resilient generation inside the proven BuilderBridge."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.adapter = ResilientOpenRouterAdapter()
        self.builder = BuilderBridge(self.root, adapter=self.adapter)

    def build(self, capability, module_name, mission, targeted_test=None):
        return self.builder.build(
            capability=capability,
            module_name=module_name,
            mission=mission,
            targeted_test=targeted_test,
        )
