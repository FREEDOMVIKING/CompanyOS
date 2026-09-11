from datetime import datetime, timezone, timedelta

class DeferredRecoveryPolicy:
    """836: bounded defer scheduling when escalation is exhausted."""

    def build(self, mission, delay_seconds, reason, provider_hint=None):
        m = dict(mission or {})
        ctx = dict(m.get("context") or {})
        m["status"] = "deferred"
        m["attempts"] = int(m.get("attempts",0)) + 1
        m["retry_after"] = (
            datetime.now(timezone.utc) + timedelta(seconds=max(60, int(delay_seconds)))
        ).isoformat()
        ctx["defer_reason"] = reason
        if provider_hint:
            ctx["provider_hint"] = provider_hint
        m["context"] = ctx
        return m
