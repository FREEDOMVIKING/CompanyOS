class BottleneckDetector:
    """652: identify the most important operational bottleneck."""

    def detect(self, state):
        candidates=[]
        backlog=int(state.get("support_backlog",0))
        critical=int(state.get("critical_incidents",0))
        churn=float(state.get("churn_rate",0))
        activation=float(state.get("activation_rate",1))
        if critical: candidates.append(("reliability",100+critical))
        if backlog>20: candidates.append(("support_capacity",backlog))
        if churn>0.08: candidates.append(("retention",churn*100))
        if activation<0.2: candidates.append(("activation",50-(activation*100)))
        candidates.sort(key=lambda x:x[1],reverse=True)
        return {
            "bottleneck":candidates[0][0] if candidates else None,
            "candidates":[{"area":a,"severity":round(s,2)} for a,s in candidates],
        }
