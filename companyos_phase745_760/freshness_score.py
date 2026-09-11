from datetime import datetime, timezone
class FreshnessScore:
    """750: freshness scoring with bounded age decay."""
    def score(self, item):
        ts = item.get("published_at") or item.get("timestamp")
        if not ts:
            return 0.5
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z","+00:00"))
            age_days = max(0, (datetime.now(timezone.utc)-dt).days)
            if age_days <= 7: return 1.0
            if age_days <= 30: return 0.8
            if age_days <= 180: return 0.6
            if age_days <= 365: return 0.4
            return 0.2
        except Exception:
            return 0.5
