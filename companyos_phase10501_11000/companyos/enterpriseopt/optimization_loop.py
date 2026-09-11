class EnterpriseOptimizationLoop:
    def next_actions(self, scorecard, pruning, capacity, risk):
        actions=[]
        for p in pruning or []:
            if p["action"]=="scale": actions.append({"venture_id":p["venture_id"],"action":"increase_resources"})
            elif p["action"]=="retire_candidate": actions.append({"venture_id":p["venture_id"],"action":"prepare_retirement_review"})
        for d in capacity or []:
            if d["action"]!="normal": actions.append({"department":d.get("name"),"action":d["action"]})
        if (risk or {}).get("high_concentration"):
            actions.append({"portfolio":"all","action":"reduce_concentration_risk"})
        return actions
