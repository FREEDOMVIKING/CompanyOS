class OfferOptimizer:
    def optimize(self, offers):
        out=[]
        for o in offers or []:
            value=float(o.get("value_score",0)); friction=float(o.get("friction",0))
            proof=float(o.get("proof",0)); margin=float(o.get("margin",0))
            score=value*.35+(1-friction)*.2+proof*.2+margin*.25
            out.append({**o,"offer_score":round(score,4)})
        return sorted(out,key=lambda x:x["offer_score"],reverse=True)
