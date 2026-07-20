from pathlib import Path
from .capability_gap_detector import CapabilityGapDetector
from .build_spec_generator import BuildSpecGenerator
from .isolated_workspace import IsolatedWorkspace
from .build_test_repair import BuildTestRepairLoop
from .git_checkpoint import GitCheckpointManager
from .self_integration import SelfIntegrationEngine
from .runtime_supervisor import RuntimeSupervisor

class SelfBuildingRuntime:
    """212: real filesystem/test/integration pipeline for autonomous self-building."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.gaps = CapabilityGapDetector()
        self.specs = BuildSpecGenerator()
        self.workspaces = IsolatedWorkspace()
        self.verifier = BuildTestRepairLoop()
        self.git = GitCheckpointManager()
        self.integrator = SelfIntegrationEngine()
        self.supervisor = RuntimeSupervisor(self.root)

    def inspect(self, goals, capabilities):
        gaps = self.gaps.detect(goals, capabilities, self.root)
        specs = [self.specs.generate(g) for g in gaps]
        return {
            "success": True,
            "project_root": str(self.root),
            "gaps": gaps,
            "build_specs": specs,
            "git": self.git.checkpoint(self.root),
            "heartbeat": self.supervisor.heartbeat("healthy"),
            "self_building_runtime": True,
            "autonomy_mode": "high",
        }

    def verify_workspace(self, workspace, targeted_test=None):
        return self.verifier.bounded_cycle(
            workspace, repair_callback=None, max_attempts=1,
            targeted_test=targeted_test
        )
