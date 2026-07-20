class PerformanceCompounder:
    """185: turn successful patterns into stronger default operating policies."""
    def learn(self,patterns):
        out=[]
        for p in patterns:
            success=float(p.get("success_rate",0));runs=int(p.get("runs",0));gain=float(p.get("gain",0))
            promote=runs>=3 and success>=.7 and gain>0
            out.append({**p,"promote_to_default":promote,"confidence":round(min(1,runs/10)*success,4)})
        return out
