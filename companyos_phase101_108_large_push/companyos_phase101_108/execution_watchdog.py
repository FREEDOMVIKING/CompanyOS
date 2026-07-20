class ExecutionWatchdog:
    """104: detect stalled, failed, and over-budget internal work."""
    def inspect(self,tasks):
        alerts=[]
        for t in tasks:
            if t.get("status")=="failed": alerts.append({"id":t.get("id"),"type":"failed"})
            elif t.get("status")=="active" and float(t.get("age",0))>float(t.get("max_age",999999)):
                alerts.append({"id":t.get("id"),"type":"stalled"})
            if float(t.get("spent",0))>float(t.get("budget",float("inf"))):
                alerts.append({"id":t.get("id"),"type":"over_budget"})
        return {"alerts":alerts,"attention_required":bool(alerts)}
