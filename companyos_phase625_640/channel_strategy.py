class ChannelStrategy:
    """628: prioritize acquisition channels by fit and evidence."""

    def rank(self, channels):
        scored = []
        for c in channels or []:
            fit=float(c.get("audience_fit",0))
            intent=float(c.get("commercial_intent",0))
            cost=max(0,float(c.get("estimated_cost",0)))
            score=(fit*0.5)+(intent*0.5)-(min(cost,10)*0.1)
            scored.append({**c,"channel_score":round(score,3)})
        return sorted(scored,key=lambda x:x["channel_score"],reverse=True)
