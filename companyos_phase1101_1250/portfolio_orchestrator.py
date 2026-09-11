class PortfolioOrchestrator:
    """1229-1240: decide scale/hold/repair/retire across ventures."""
    def decide(self, ventures):
        decisions=[]
        for v in ventures or []:
            score=float(v.get("kpi_score",0))
            health=v.get("health","healthy")
            revenue=float(v.get("net_revenue",0))
            if health!="healthy":
                action="repair"
            elif score>=0.7 and revenue>0:
                action="scale"
            elif score>=0.45:
                action="hold_optimize"
            elif revenue<=0 and score<0.3:
                action="retire_candidate"
            else:
                action="observe"
            decisions.append({"venture_id":v.get("venture_id"),"action":action,"score":score})
        return decisions
