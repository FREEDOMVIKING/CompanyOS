class StrategyEngine:
    """102: rank strategic options by value, evidence, speed, and risk."""
    def rank(self, options):
        out=[]
        for x in options:
            value=float(x.get("value",0)); evidence=float(x.get("evidence",0))
            speed=float(x.get("speed",0)); risk=float(x.get("risk",0))
            score=value*.35+evidence*.30+speed*.20+(1-risk)*.15
            out.append({**x,"strategy_score":round(score,4)})
        return sorted(out,key=lambda x:x["strategy_score"],reverse=True)
