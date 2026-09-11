class ConcentrationRisk:
    """682: detect customer/category/revenue concentration."""

    def evaluate(self, ventures):
        total=sum(float(v.get("mrr",0)) for v in ventures) or 1.0
        shares=[
            {"venture_id":v.get("venture_id"),"share":round(float(v.get("mrr",0))/total,4)}
            for v in ventures
        ]
        dominant=max(shares,key=lambda x:x["share"]) if shares else None
        return {
            "dominant_venture":dominant,
            "high_revenue_concentration":bool(dominant and dominant["share"] > 0.7 and len(ventures) >= 2),
        }
