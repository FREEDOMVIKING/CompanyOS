class PartnerOpportunityEngine:
    def rank(self, partners):
        rows=[]
        for p in partners or []:
            reach=float(p.get("reach",0))
            trust=float(p.get("trust",0))
            fit=float(p.get("strategic_fit",0))
            economics=float(p.get("economic_value",0))
            score=reach*.25+trust*.25+fit*.3+economics*.2
            rows.append({**p,"partner_score":round(score,4)})
        return sorted(rows,key=lambda x:x["partner_score"],reverse=True)
