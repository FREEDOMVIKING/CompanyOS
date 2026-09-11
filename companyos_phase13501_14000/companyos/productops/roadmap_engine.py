class ProductRoadmapEngine:
    def prioritize(self, initiatives):
        rows=[]
        for i in initiatives or []:
            value=float(i.get("customer_value",0))
            strategy=float(i.get("strategic_fit",0))
            evidence=float(i.get("evidence",0))
            effort=max(.1,float(i.get("effort",1)))
            risk=float(i.get("risk",0))
            score=(value*.35+strategy*.25+evidence*.25+(1-risk)*.15)/effort
            rows.append({**i,"roadmap_score":round(score,4)})
        return sorted(rows,key=lambda x:x["roadmap_score"],reverse=True)
