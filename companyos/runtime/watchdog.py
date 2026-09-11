from datetime import datetime, timezone

class RuntimeWatchdog:
    def evaluate(self, heartbeat, max_age_seconds=180):
        if not heartbeat or not heartbeat.get("timestamp"):
            return {"healthy":False,"action":"restart_service","reason":"missing_heartbeat"}
        try:
            ts=datetime.fromisoformat(heartbeat["timestamp"])
            age=(datetime.now(timezone.utc)-ts).total_seconds()
        except Exception:
            return {"healthy":False,"action":"restart_service","reason":"invalid_heartbeat"}
        if age>max_age_seconds:
            return {"healthy":False,"action":"restart_service","reason":"stale_heartbeat","age_seconds":round(age,2)}
        return {"healthy":True,"action":"none","reason":"heartbeat_fresh","age_seconds":round(age,2)}
