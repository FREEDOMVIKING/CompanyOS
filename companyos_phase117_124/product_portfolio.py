class ProductPortfolio:
    """119: compare product bets and recommend resource posture."""
    def review(self,products):
        out=[]
        for p in products:
            traction=float(p.get("traction",0));margin=float(p.get("margin",0));fit=float(p.get("fit",0));risk=float(p.get("risk",0))
            score=traction*.35+margin*.25+fit*.25+(1-risk)*.15
            action="invest" if score>=.75 else "validate" if score>=.45 else "pause_review"
            out.append({**p,"score":round(score,4),"recommendation":action})
        return sorted(out,key=lambda x:x["score"],reverse=True)
