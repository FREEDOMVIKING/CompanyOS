class SLATracker:
    """649: response/resolution target tracking."""

    def evaluate(self, tickets):
        total=len(tickets or [])
        if total==0:
            return {"total":0,"within_target_rate":1.0,"breaches":[]}
        breaches=[t for t in tickets if not t.get("within_target",False)]
        return {
            "total":total,
            "within_target_rate":round((total-len(breaches))/total,4),
            "breaches":breaches,
        }
