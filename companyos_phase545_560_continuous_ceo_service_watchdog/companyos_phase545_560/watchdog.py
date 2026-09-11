from datetime import datetime, timezone

class CEOWatchdog:
    """556: detect stale or unhealthy continuous-service state."""

    def evaluate(self, state, stale_seconds=900):
        last = state.get("last_tick_at")
        if not last:
            return {"healthy":False,"reason":"no_tick_recorded"}
        try:
            dt = datetime.fromisoformat(str(last).replace("Z","+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - dt).total_seconds()
        except Exception:
            return {"healthy":False,"reason":"invalid_timestamp"}

        if age > int(stale_seconds):
            return {"healthy":False,"reason":"stale","age_seconds":int(age)}
        if int(state.get("consecutive_failures",0)) >= 5:
            return {"healthy":False,"reason":"failure_threshold"}
        return {"healthy":True,"reason":"healthy","age_seconds":int(age)}
