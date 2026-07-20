from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict

from .agent_router import AgentRouter
from .approval_guard import ApprovalGuard
from .health_supervisor import HealthSupervisor
from .portfolio_manager import PortfolioManager

class AutonomousCycleEngine:
    """Phase 60: bounded autonomous internal cycle coordinator."""
    def __init__(self):
        self.router = AgentRouter()
        self.guard = ApprovalGuard()
        self.health = HealthSupervisor()
        self.portfolio = PortfolioManager()

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        tasks = payload.get("tasks", [])
        routed = [{**t, "assigned_role": self.router.route(t)} for t in tasks]
        actions = payload.get("actions", [])
        guarded = [{**a, "guard": self.guard.evaluate(a)} for a in actions]
        return {
            "success": True,
            "status": "phase60_cycle_completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tasks": routed,
            "actions": guarded,
            "portfolio": self.portfolio.rank(payload.get("ventures", [])),
            "health": self.health.evaluate(payload.get("health_checks", {})),
            "external_action_taken": False,
        }
