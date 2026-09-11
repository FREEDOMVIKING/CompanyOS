from companyos_phase481_496 import MissionOrchestrator

class MissionExecutor:
    """709: unified mission execution wrapper."""

    def __init__(self, root):
        self.runner = MissionOrchestrator(root)

    def execute(self, mission):
        result = self.runner.run(mission)
        return {
            "mission_id": mission.get("mission_id"),
            "mission_type": mission.get("mission_type"),
            "success": bool(result.get("success")),
            "status": result.get("status"),
            "result": result,
        }
