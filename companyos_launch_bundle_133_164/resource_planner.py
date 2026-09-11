from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ResourcePlan:
    project_id: str
    cpu_budget: int
    memory_budget_mb: int
    max_parallel_tasks: int
    priority: int

class ResourcePlanner:
    def plan(self, project_id, priority=100, complexity=1):
        complexity=max(1,int(complexity))
        return ResourcePlan(project_id, 1+complexity, 256*complexity, min(8,1+complexity), int(priority))
