from datetime import datetime, timezone

class HealthSnapshot:
    """555: concise CEO service health snapshot."""

    def build(self, state, tick_result=None):
        return {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "running":bool(state.get("running")),
            "ticks":int(state.get("ticks",0)),
            "consecutive_failures":int(state.get("consecutive_failures",0)),
            "last_status":state.get("last_status"),
            "last_tick_at":state.get("last_tick_at"),
            "last_tick_success":None if tick_result is None else bool(tick_result.get("success")),
        }
