from __future__ import annotations
import os
from pathlib import Path

from companyos_phase221_228 import RealCoderLoop, CoderBridge
from .provider_config import ProviderConfig
from .coder_command_builder import CoderCommandBuilder
from .connection_probe import ConnectionProbe
from .model_mission_runner import ModelMissionRunner
from .self_build_daemon import SelfBuildDaemon
from .build_audit import BuildAudit
from .handoff_controller import HandoffController

class ModelConnectedRuntime:
    """236: activate and assess the real model-connected self-building runtime."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.provider = ProviderConfig(self.root)
        self.command_builder = CoderCommandBuilder()
        self.probe = ConnectionProbe()
        self.daemon = SelfBuildDaemon(self.root)
        self.audit = BuildAudit(self.root)
        self.handoff = HandoffController()

    def status(self):
        cfg = self.provider.load()
        command = os.environ.get("COMPANYOS_CODER_CMD", "").strip()
        bridge = CoderBridge(command=command)

        return {
            "success": True,
            "status": "phase236_model_connected_runtime_ready",
            "provider_configured": bool(cfg),
            "external_coder_configured": bridge.configured,
            "provider_secret_available": self.provider.secret_available(cfg) if cfg else False,
            "suggested_coder_command": self.command_builder.build(self.root),
            "autonomy_mode": "high",
        }

    def build_loop(self):
        command = os.environ.get("COMPANYOS_CODER_CMD", "").strip()
        return RealCoderLoop(self.root, bridge=CoderBridge(command=command))

    def evaluate_handoff(self, rollback_available=False):
        s = self.status()
        return self.handoff.evaluate({
            "real_filesystem_workspace": True,
            "real_test_execution": True,
            "live_integration": True,
            "rollback_available": rollback_available,
            "coder_connected": s["external_coder_configured"],
            "persistent_runtime": True,
        })
