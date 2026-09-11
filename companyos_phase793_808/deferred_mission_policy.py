from datetime import datetime, timezone, timedelta

class DeferredMissionPolicy:
    """799: create bounded follow-up research mission when evidence is insufficient."""

    def build(self, mission, fallback_provider=None, delay_seconds=300):
        m = dict(mission or {})
        context = dict(m.get("context") or {})
        m["attempts"] = int(m.get("attempts", 0)) + 1
        m["status"] = "deferred"
        m["retry_after"] = (
            datetime.now(timezone.utc) + timedelta(seconds=max(30, int(delay_seconds)))
        ).isoformat()

        if fallback_provider:
            context["provider_hint"] = fallback_provider
        context["defer_reason"] = "insufficient_research_evidence"
        m["context"] = context
        return m
