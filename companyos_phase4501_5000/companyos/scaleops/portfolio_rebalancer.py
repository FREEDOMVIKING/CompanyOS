class PortfolioRebalancer:
    def rebalance(self, ventures):
        actions=[]
        for v in ventures or []:
            score=float(v.get("score",0))
            cashflow=float(v.get("cashflow",0))
            if score>=.75 and cashflow>=0:
                action="increase_allocation"
            elif score>=.5:
                action="hold_and_optimize"
            elif score<.3 and cashflow<0:
                action="reduce_or_exit"
            else:
                action="observe"
            actions.append({"venture_id":v.get("venture_id"),"action":action})
        return actions
