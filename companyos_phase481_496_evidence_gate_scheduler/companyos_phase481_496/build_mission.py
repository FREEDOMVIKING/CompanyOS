from companyos_phase417_432 import AutonomousBuildBridge

class BuildMission:
    """491: bounded autonomous build preparation mission."""

    def __init__(self):
        self.bridge = AutonomousBuildBridge()

    def run(self, context=None):
        context = context or {}
        packet = context.get("venture_packet")
        if not packet:
            return {"success":False,"status":"build_mission_missing_packet","mission_type":"build","data":{}}

        result = self.bridge.prepare_build(packet)
        return {
            "success":bool(result.get("success")),
            "status":result.get("status","build_mission_complete"),
            "mission_type":"build",
            "data":{"build_packet":result},
        }
