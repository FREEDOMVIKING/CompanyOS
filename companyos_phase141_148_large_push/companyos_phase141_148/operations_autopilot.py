from __future__ import annotations
from typing import Any, Dict, List

class OperationsAutopilot:
    """144: autonomously handle routine internal operations and recovery."""

    SAFE_ACTIONS = {
        "restart_worker",
        "requeue_task",
        "rotate_internal_log",
        "refresh_cache",
        "rebuild_index",
        "retry_dependency",
        "run_healthcheck",
    }

    def decide(self, incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for incident in incidents:
            proposed = str(incident.get("proposed_action", "run_healthcheck"))
            safe = proposed in self.SAFE_ACTIONS and not bool(incident.get("destructive", False))
            out.append({
                **incident,
                "autonomous_action_allowed": safe,
                "approval_required": not safe,
            })
        return out
