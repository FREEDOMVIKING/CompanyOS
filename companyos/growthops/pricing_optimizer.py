class PricingOptimizer:
    def evaluate(self, offers):
        out=[]
        for o in offers or []:
            conversion=float(o.get("conversion",0)); price=float(o.get("price",0))
            margin=float(o.get("margin",0))
            score=conversion*price*max(0,margin)
            out.append({**o,"economic_score":round(score,3)})
        return sorted(out,key=lambda x:x["economic_score"],reverse=True)
