from datetime import datetime, timezone
class EventBus:
    def publish(self, kind, payload=None):
        return {
            "kind": kind,
            "payload": payload or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
