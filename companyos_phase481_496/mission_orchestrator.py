from .research_mission import ResearchMission
from .validation_mission import ValidationMission
from .venture_mission import VentureMission
from .build_mission import BuildMission
from .operations_mission import OperationsMission
from .portfolio_mission import PortfolioMission

class MissionOrchestrator:
    """494: execute canonical CEO missions under one interface."""

    def __init__(self, root):
        self.handlers = {
            "research":ResearchMission(root),
            "validation":ValidationMission(),
            "venture":VentureMission(),
            "build":BuildMission(),
            "operations":OperationsMission(),
            "portfolio":PortfolioMission(),
        }

    def run(self, mission):
        typ = mission.get("mission_type")
        handler = self.handlers.get(typ)
        if not handler:
            return {"success":False,"status":"unknown_mission_type","mission_type":typ,"data":{}}
        return handler.run(mission.get("context") or {})
