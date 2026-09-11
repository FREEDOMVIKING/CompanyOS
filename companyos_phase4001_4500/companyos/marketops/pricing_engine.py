class PricingEngine:
    def recommend(self, offers):
        ranked=[]
        for o in offers or []:
            price=float(o.get("price",0))
            conv=float(o.get("conversion_rate",0))
            retention=float(o.get("retention_rate",0))
            margin=float(o.get("gross_margin",0))
            revenue_per_visitor=price*conv
            score=min(1,revenue_per_visitor/100)*0.35+retention*0.3+margin*0.35
            ranked.append({**o,"revenue_per_visitor":round(revenue_per_visitor,2),"pricing_score":round(score,4)})
        ranked=sorted(ranked,key=lambda x:x["pricing_score"],reverse=True)
        return {"winner":ranked[0] if ranked else None,"ranked":ranked}
