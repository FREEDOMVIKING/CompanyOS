class DecisionConvergence:
    """880: determine if repeated decisions have converged."""
    def evaluate(self,history):
        h=list(history or [])
        if not h:return {"converged":False,"decision":None}
        last=h[-1]
        if last.get("decision") in ("GO","KILL"):
            return {"converged":True,"decision":last.get("decision")}
        if len(h)>=2 and h[-1].get("decision")==h[-2].get("decision")=="REVISE":
            delta=abs(float(h[-1].get("confidence",0))-float(h[-2].get("confidence",0)))
            if delta<0.02:return {"converged":True,"decision":"STALLED_REVISE"}
        return {"converged":False,"decision":last.get("decision")}
