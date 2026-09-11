from __future__ import annotations
from datetime import datetime, timezone, timedelta

class FreshnessFilter:
    """340: filter timestamped evidence while retaining undated problem evidence."""

    def filter(self, records, max_age_days=365):
        cutoff = datetime.now(timezone.utc) - timedelta(days=int(max_age_days))
        out = []
        for r in records:
            published = r.get("published_at")
            if not published:
                out.append(r)
                continue
            try:
                dt = datetime.fromisoformat(str(published).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt >= cutoff:
                    out.append(r)
            except Exception:
                out.append(r)
        return out
