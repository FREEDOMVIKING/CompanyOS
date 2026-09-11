from datetime import datetime,timezone,timedelta
class MissionRescheduler:
    def reschedule(self,mission,delay_seconds,reason,fallback_provider=None):
        m=dict(mission or {}); ctx=dict(m.get("context") or {})
        m["attempts"]=int(m.get("attempts",0))+1
        m["status"]="deferred"
        m["retry_after"]=(datetime.now(timezone.utc)+timedelta(seconds=int(delay_seconds))).isoformat()
        ctx["defer_reason"]=reason
        if fallback_provider: ctx["provider_hint"]=fallback_provider
        m["context"]=ctx
        return m
