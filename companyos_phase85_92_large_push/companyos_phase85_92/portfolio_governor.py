class PortfolioGovernor:
    """90: portfolio-level continue/hold/stop recommendations."""
    def review(self,ventures):
        out=[]
        for v in ventures:
            traction=float(v.get("traction",0)); strategic=float(v.get("strategic_fit",0))
            risk=float(v.get("risk",0)); burn=float(v.get("burn_pressure",0))
            score=traction*.4+strategic*.3+(1-risk)*.2+(1-burn)*.1
            action="continue" if score>=.7 else "hold_and_validate" if score>=.45 else "consider_stop"
            out.append({**v,"governance_score":round(score,4),"recommendation":action})
        return sorted(out,key=lambda x:x["governance_score"],reverse=True)
