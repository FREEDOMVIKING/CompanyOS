class CapitalAttention:
    """568: allocate bounded CEO attention without moving money automatically."""

    def allocate(self, ranked, active_limit=2):
        active = ranked[:max(1,int(active_limit))]
        waiting = ranked[len(active):]
        return {
            "active_attention":[v.get("venture_id") for v in active],
            "waiting":[v.get("venture_id") for v in waiting],
            "automatic_financial_actions":False,
        }
