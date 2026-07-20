class NorthStarManager:
    """181: align self-generated work to durable company objectives."""
    def align(self,initiatives,north_star):
        rows=[]
        for x in initiatives:
            relevance=float(x.get("relevance",0));impact=float(x.get("impact",0));evidence=float(x.get("evidence",0))
            score=relevance*.45+impact*.35+evidence*.20
            rows.append({**x,"north_star":north_star,"alignment_score":round(score,4),"continue":score>=.35})
        return sorted(rows,key=lambda x:x["alignment_score"],reverse=True)
