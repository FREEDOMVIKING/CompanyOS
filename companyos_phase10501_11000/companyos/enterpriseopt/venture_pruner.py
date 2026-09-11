class VenturePruner:
    def decide(self, ventures):
        out=[]
        for v in ventures or []:
            score=float(v.get("enterprise_score",0))
            cashflow=float(v.get("cashflow",0))
            trend=float(v.get("trend",0))
            if score>=.75 and cashflow>=0:
                action="scale"
            elif score>=.5:
                action="optimize"
            elif score<.3 and cashflow<0 and trend<=0:
                action="retire_candidate"
            else:
                action="observe"
            out.append({"venture_id":v.get("venture_id"),"action":action})
        return out
