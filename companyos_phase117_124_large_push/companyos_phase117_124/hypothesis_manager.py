class HypothesisManager:
    """117: prioritize testable business hypotheses."""
    def rank(self,items):
        out=[]
        for x in items:
            impact=float(x.get("impact",0));confidence=float(x.get("confidence",0));ease=float(x.get("ease",0))
            score=impact*.4+confidence*.35+ease*.25
            out.append({**x,"hypothesis_score":round(score,4),"status":x.get("status","untested")})
        return sorted(out,key=lambda z:z["hypothesis_score"],reverse=True)
