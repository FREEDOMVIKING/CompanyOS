from __future__ import annotations
from dataclasses import dataclass
from companyos.runtime.project_pipeline import ProjectPipeline
from companyos.runtime.specialist_coordination import SpecialistCoordinator
from companyos.runtime.project_checkpointing import ProjectCheckpointStore
from companyos.runtime.decision_journal import DecisionJournal

@dataclass(frozen=True)
class InternalCycleResult:
    project_id: str
    stage_before: str
    stage_after: str
    agent: str
    advanced: bool

class AutonomousInternalCycle:
    def __init__(self):
        self.projects=ProjectPipeline()
        self.coord=SpecialistCoordinator()
        self.cp=ProjectCheckpointStore()
        self.journal=DecisionJournal()

    def run(self,project_id):
        r=self.projects.load(project_id)
        before=r.stage
        a=self.coord.assignment_for(before)
        self.cp.write(project_id,before,{"agent":a.agent_name})
        if before not in ("COMPLETED","BLOCKED","FAILED"):
            r=self.projects.advance(project_id)
            advanced=True
        else:
            advanced=False
        self.journal.append("project_cycle",project_id,r.stage,{"agent":a.agent_name})
        return InternalCycleResult(project_id,before,r.stage,a.agent_name,advanced)
