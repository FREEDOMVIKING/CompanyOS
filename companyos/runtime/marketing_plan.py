from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class MarketingPlan:
    project_id: str
    audience: str
    positioning: str
    channels: tuple[str,...]
    external_execution_required: bool

class MarketingPlanner:
    def build(self,project_id,audience,positioning,channels):
        return MarketingPlan(project_id,audience,positioning,tuple(channels),True)
