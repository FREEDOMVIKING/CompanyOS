from __future__ import annotations
from companyos_phase221_228 import RealCoderLoop, CoderBridge

class AutonomousBuildRunner:
    """242: launch one real model-written self-build mission."""

    def __init__(self, project_root, coder_command):
        self.loop = RealCoderLoop(project_root, bridge=CoderBridge(command=coder_command))

    def run(self, mission, capabilities=None, max_attempts=3):
        goals = [{
            "goal": mission["goal"],
            "required_capabilities": mission["required_capabilities"],
            "priority": mission.get("priority", 1.0),
        }]
        return self.loop.build_selected_gap(
            goals,
            capabilities or [],
            max_attempts=max_attempts,
        )
