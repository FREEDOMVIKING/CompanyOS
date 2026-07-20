class StagnationBreaker:
    """163: automatically change tactics when repeated cycles stop improving."""
    def decide(self,history):
        if len(history)<3: return {"stagnant":False,"action":"continue"}
        recent=[float(x.get("score",0)) for x in history[-3:]]
        stagnant=max(recent)-min(recent)<.03
        return {"stagnant":stagnant,"action":"generate_alternative_strategy" if stagnant else "continue"}
