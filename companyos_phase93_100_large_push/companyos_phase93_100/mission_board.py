from __future__ import annotations
from typing import Any, Dict, List

class MissionBoard:
    """93: mission lifecycle board with deterministic state transitions."""
    ALLOWED = {
        "queued": {"active", "cancelled"},
        "active": {"blocked", "review", "completed", "cancelled"},
        "blocked": {"active", "cancelled"},
        "review": {"active", "completed"},
        "completed": set(),
        "cancelled": set(),
    }

    def transition(self, mission: Dict[str, Any], new_status: str) -> Dict[str, Any]:
        current = str(mission.get("status", "queued"))
        if new_status not in self.ALLOWED.get(current, set()):
            return {**mission, "transition_ok": False, "transition_error": f"{current}->{new_status} not allowed"}
        return {**mission, "status": new_status, "transition_ok": True}
