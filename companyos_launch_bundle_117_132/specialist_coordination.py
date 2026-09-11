from __future__ import annotations

from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class SpecialistAssignment:
    stage: str
    agent_name: str
    responsibility: str

class SpecialistCoordinator:
    ROUTES = {
        "DISCOVERY": ("research_agent", "collect and organize internal discovery findings"),
        "VALIDATION": ("validation_agent", "evaluate feasibility, evidence, and risks"),
        "PLANNING": ("planning_agent", "create implementation plan and milestones"),
        "BUILD": ("builder_agent", "produce internal build artifacts"),
        "QA": ("qa_agent", "test artifacts and surface defects"),
        "LAUNCH_READY": ("launch_readiness_agent", "prepare launch checklist and approvals"),
    }

    def assignment_for(self, stage: str) -> SpecialistAssignment:
        agent, resp = self.ROUTES.get(stage, ("generalist_agent", "handle internal project work"))
        return SpecialistAssignment(stage=stage, agent_name=agent, responsibility=resp)
