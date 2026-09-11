class OfferOptimizer:
    """1131-1140: optimize offer/pricing using validation and live conversion signals."""
    def recommend(self, offers):
        ranked=[]
        for o in offers or []:
            traffic=max(1,float(o.get("traffic",0)))
            conversions=float(o.get("conversions",0))
            revenue=float(o.get("revenue",0))
            conversion=conversions/traffic
            rev_per_visit=revenue/traffic
            score=conversion*0.55+min(1.0,rev_per_visit/100)*0.45
            ranked.append({**o,"conversion_rate":round(conversion,4),"revenue_per_visit":round(rev_per_visit,2),"score":round(score,4)})
        ranked=sorted(ranked,key=lambda x:x["score"],reverse=True)
        return {"winner":ranked[0] if ranked else None,"ranked":ranked}
