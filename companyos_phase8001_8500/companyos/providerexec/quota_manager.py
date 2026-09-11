class QuotaManager:
    def evaluate(self, used, limit, reserve_ratio=.1):
        used=float(used); limit=max(1,float(limit))
        remaining=max(0,limit-used)
        reserve=limit*float(reserve_ratio)
        return {
            "used":used,
            "limit":limit,
            "remaining":remaining,
            "within_quota":remaining>reserve,
            "action":"normal" if remaining>reserve else "throttle_or_fallback"
        }
