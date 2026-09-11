class SuccessionEngine:
    """685: replace weak ventures with stronger candidates when capacity is bounded."""

    def recommend(self, active, candidates, max_active=3):
        active_sorted=sorted(active,key=lambda v:float(v.get("portfolio_score",0)),reverse=True)
        candidate_sorted=sorted(candidates,key=lambda v:float(v.get("portfolio_score",0)),reverse=True)

        if len(active_sorted) < max_active and candidate_sorted:
            return {"action":"spin_up","candidate":candidate_sorted[0]}

        if not active_sorted or not candidate_sorted:
            return {"action":"hold"}

        weakest=active_sorted[-1]
        strongest=candidate_sorted[0]
        if float(strongest.get("portfolio_score",0)) >= float(weakest.get("portfolio_score",0)) + 2:
            return {
                "action":"replace",
                "pause_or_kill":weakest.get("venture_id"),
                "spin_up":strongest.get("venture_id"),
            }
        return {"action":"hold"}
