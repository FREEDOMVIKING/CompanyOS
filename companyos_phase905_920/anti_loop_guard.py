class AntiLoopGuard:
    """917: block repeated identical adaptive strategies."""
    def evaluate(self, history):
        h=list(history or [])
        if len(h)<2:return {"looping":False}
        a=h[-1]; b=h[-2]
        same_query=a.get("query")==b.get("query")
        same_providers=a.get("providers")==b.get("providers")
        return {"looping":bool(same_query and same_providers)}
