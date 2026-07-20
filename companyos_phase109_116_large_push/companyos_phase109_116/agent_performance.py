class AgentPerformance:
    """113: score specialist agents from quality, reliability, speed, and cost."""
    def score(self,agents):
        out=[]
        for a in agents:
            q=float(a.get("quality",0));r=float(a.get("reliability",0));s=float(a.get("speed",0));c=float(a.get("cost_efficiency",0))
            score=q*.35+r*.30+s*.20+c*.15
            out.append({**a,"performance_score":round(score,4)})
        return sorted(out,key=lambda x:x["performance_score"],reverse=True)
