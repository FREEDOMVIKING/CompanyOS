from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict

from .objective_manager import ObjectiveManager
from .task_graph import TaskGraph
from .resource_planner import ResourcePlanner
from .delegation_engine import DelegationEngine
from .governance_engine import GovernanceEngine

class ExecutiveLoop:
    """Phase 68: unified strategic planning cycle for internal autonomous work."""
    def __init__(self):
        self.objectives = ObjectiveManager()
        self.graph = TaskGraph()
        self.resources = ResourcePlanner()
        self.delegation = DelegationEngine()
        self.governance = GovernanceEngine()

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        objectives = self.objectives.prioritize(payload.get("objectives", []))
        graph = self.graph.order(payload.get("tasks", []))
        ordered_tasks = graph.get("ordered", [])
        allocation = self.resources.allocate(ordered_tasks, payload.get("capacity", 0))
        delegated = self.delegation.assign(allocation["chosen"], payload.get("agents", []))
        actions = [
            {**a, "governance": self.governance.classify(a)}
            for a in payload.get("actions", [])
        ]
        return {
            "success": graph["success"],
            "status": "phase68_executive_cycle_completed" if graph["success"] else graph["status"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "objectives": objectives,
            "task_graph": graph,
            "allocation": allocation,
            "delegated_tasks": delegated,
            "actions": actions,
            "external_action_taken": False,
        }
