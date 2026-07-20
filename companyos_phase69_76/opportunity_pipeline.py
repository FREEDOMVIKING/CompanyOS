from typing import Any, Dict, List
class OpportunityPipeline:
    """69: score and stage business opportunities."""
    def rank(self, items: List[Dict[str,Any]]):
        out=[]
        for x in items:
            demand=float(x.get("demand",0)); margin=float(x.get("margin",0))
            speed=float(x.get("speed",0)); confidence=float(x.get("confidence",.5))
            risk=float(x.get("risk",.5))
            score=(demand*.30+margin*.25+speed*.20+confidence*100*.25)*(1-min(1,risk)*.45)
            out.append({**x,"opportunity_score":round(score,4)})
        return sorted(out,key=lambda z:z["opportunity_score"],reverse=True)
