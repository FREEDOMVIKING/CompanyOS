from __future__ import annotations
from dataclasses import dataclass
from companyos.runtime.project_pipeline import ProjectPipeline

@dataclass(frozen=True)
class PortfolioSummary:
    total_projects: int
    active_projects: int
    completed_projects: int
    blocked_projects: int

class PortfolioManager:
    def summary(self):
        records=ProjectPipeline().all()
        return PortfolioSummary(
            total_projects=len(records),
            active_projects=sum(1 for r in records if r.state=="ACTIVE"),
            completed_projects=sum(1 for r in records if r.state=="COMPLETED"),
            blocked_projects=sum(1 for r in records if r.stage=="BLOCKED"),
        )
