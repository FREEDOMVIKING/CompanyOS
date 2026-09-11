from __future__ import annotations
from dataclasses import dataclass
from companyos.runtime.project_pipeline import ProjectPipeline
from companyos.runtime.specialist_coordination import SpecialistCoordinator
from companyos.runtime.project_checkpointing import ProjectCheckpointStore

@dataclass(frozen=True)
class OperationsCycle:
    project_id: str
    stage_before: str
    stage_after: str
    assigned_agent: str
    checkpoint_written: bool

class OperationsLoop:
    """
    One bounded internal project advancement cycle.
    """
    def __init__(self):
        self.projects=ProjectPipeline()
        self.coordinator=SpecialistCoordinator()
        self.checkpoints=ProjectCheckpointStore()

    def cycle(self, project_id):
        rec=self.projects.load(project_id)
        before=rec.stage
        assignment=self.coordinator.assignment_for(before)
        self.checkpoints.write(project_id,before,{
            "state":rec.state,
            "stage":rec.stage,
            "agent":assignment.agent_name,
        })
        rec=self.projects.advance(project_id)
        return OperationsCycle(project_id,before,rec.stage,assignment.agent_name,True)
