from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List

class AuditTrail:
    """99: append-only in-memory audit records for critical decisions/actions."""
    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def record(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "event_id": f"evt-{len(self.events)+1:06d}",
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": dict(payload),
        }
        self.events.append(event)
        return event
