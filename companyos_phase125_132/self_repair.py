from __future__ import annotations
from typing import Any, Dict

class SelfRepairEngine:
    """128: autonomous bounded self-repair for reversible internal faults."""

    SAFE_AUTO_REPAIR = {
        "syntax_error",
        "test_failure",
        "missing_internal_file",
        "temporary_dependency",
        "stalled_worker",
        "queue_inconsistency",
    }

    def plan(self, fault: Dict[str, Any]) -> Dict[str, Any]:
        kind = str(fault.get("kind", "unknown"))
        attempts = int(fault.get("attempts", 0))
        if kind in self.SAFE_AUTO_REPAIR and attempts < 3:
            return {
                "action": "repair_and_verify",
                "autonomous": True,
                "max_additional_attempts": 3 - attempts,
            }
        return {
            "action": "isolate_and_escalate",
            "autonomous": False,
            "max_additional_attempts": 0,
        }
