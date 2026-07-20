from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict

from .mission_board import MissionBoard
from .autonomous_queue import AutonomousQueue
from .artifact_registry import ArtifactRegistry
from .approval_center import ApprovalCenter
from .production_readiness import ProductionReadiness
from .external_action_router import ExternalActionRouter
from .audit_trail import AuditTrail

class ProductionCEO:
    """100: production-oriented bounded CEO orchestration layer."""
    def __init__(self):
        self.missions = MissionBoard()
        self.queue = AutonomousQueue()
        self.artifacts = ArtifactRegistry()
        self.approvals = ApprovalCenter()
        self.readiness = ProductionReadiness()
        self.external = ExternalActionRouter()
        self.audit = AuditTrail()

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        tasks = self.queue.select(payload.get("tasks", []), payload.get("task_limit", 5))
        pending = self.approvals.pending(payload.get("actions", []))
        routed_actions = [self.external.route(a) for a in payload.get("actions", [])]
        readiness = self.readiness.evaluate(payload.get("readiness", {}))

        for task in tasks:
            self.audit.record("task_selected", {"task_id": task.get("id"), "title": task.get("title")})

        return {
            "success": True,
            "status": "phase100_production_ceo_cycle_completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "selected_tasks": tasks,
            "pending_approvals": pending,
            "routed_actions": routed_actions,
            "production_readiness": readiness,
            "audit_events": list(self.audit.events),
            "external_action_taken": False,
            "irreversible_action_taken": False,
        }
