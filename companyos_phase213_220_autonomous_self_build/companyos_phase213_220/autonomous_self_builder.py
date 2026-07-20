from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from companyos_phase205_212 import (
    CapabilityGapDetector,
    BuildSpecGenerator,
    IsolatedWorkspace,
    BuildTestRepairLoop,
    GitCheckpointManager,
    SelfIntegrationEngine,
    RuntimeSupervisor,
)

from .model_adapter import ModelAdapter
from .code_generator import AutonomousCodeGenerator
from .integration_gate import IntegrationGate
from .capability_registry import CapabilityRegistry
from .self_build_mission import SelfBuildMission


class AutonomousSelfBuilder:
    """220: end-to-end capability gap -> code -> tests -> integration pipeline."""

    def __init__(self, project_root, adapter=None):
        self.root = Path(project_root).resolve()
        self.adapter = adapter or ModelAdapter()
        self.gaps = CapabilityGapDetector()
        self.specs = BuildSpecGenerator()
        self.workspaces = IsolatedWorkspace()
        self.verifier = BuildTestRepairLoop()
        self.git = GitCheckpointManager()
        self.integrator = SelfIntegrationEngine()
        self.integration_gate = IntegrationGate()
        self.registry = CapabilityRegistry(self.root)
        self.supervisor = RuntimeSupervisor(self.root)
        self.generator = AutonomousCodeGenerator()
        self.missions = SelfBuildMission()

    def build_capability(
        self,
        gap: Dict[str, Any],
        verify_full_live_suite: bool = False,
    ) -> Dict[str, Any]:
        spec = self.specs.generate(gap)
        mission = self.missions.create(gap, spec)
        checkpoint = self.git.checkpoint(self.root)
        ws = self.workspaces.create(self.root)

        try:
            generation = self.generator.generate(
                self.adapter,
                ws["workspace"],
                spec,
                context={"project_root": str(self.root)},
            )
            if not generation.get("success"):
                return {
                    "success": False,
                    "stage": "generation",
                    "mission": mission,
                    "generation": generation,
                }

            target_test = f"tests/test_{spec['module_name']}.py"
            verification = self.verifier.bounded_cycle(
                ws["workspace"],
                repair_callback=None,
                max_attempts=1,
                targeted_test=target_test,
            )
            if not verification.get("success"):
                return {
                    "success": False,
                    "stage": "isolated_verification",
                    "mission": mission,
                    "verification": verification,
                }

            integration = self.integrator.integrate(
                ws["workspace"],
                self.root,
                spec["module_name"],
                verification,
            )
            if not integration.get("integrated"):
                return {
                    "success": False,
                    "stage": "integration",
                    "mission": mission,
                    "integration": integration,
                }

            live_test = None if verify_full_live_suite else target_test
            live_verification = self.integration_gate.verify_live(
                self.root,
                targeted_test=live_test,
            )

            if not live_verification.get("success"):
                rollback = self.git.restore(
                    self.root,
                    checkpoint.get("checkpoint") if checkpoint.get("available") else None,
                )
                return {
                    "success": False,
                    "stage": "live_verification",
                    "mission": mission,
                    "live_verification": live_verification,
                    "rollback": rollback,
                }

            record = {
                "module": spec["module_name"],
                "verified": True,
                "built_at": datetime.now(timezone.utc).isoformat(),
                "adapter": generation.get("metadata", {}).get("adapter", "configured_model_adapter"),
                "mission_id": mission["mission_id"],
            }
            self.registry.register(spec["capability"], record)
            self.supervisor.heartbeat("healthy")

            return {
                "success": True,
                "status": "autonomous_self_build_completed",
                "mission": mission,
                "generation": generation,
                "verification": verification,
                "integration": integration,
                "live_verification": live_verification,
                "registered_capability": record,
                "self_building": True,
                "autonomy_mode": "high",
            }
        finally:
            self.workspaces.destroy(ws["container"])
