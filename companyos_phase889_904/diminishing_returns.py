class DiminishingReturnsDetector:
    """892: detect repeated small confidence gains."""
    def evaluate(self,history,min_gain=0.02,window=2):
        h=list(history or [])
        if len(h)<window+1:
            return {"diminishing":False,"gains":[]}
        recent=h[-(window+1):]
        gains=[]
        for a,b in zip(recent,recent[1:]):
            gains.append(round(float(b.get("confidence",0))-float(a.get("confidence",0)),3))
        return {"diminishing":all(g<min_gain for g in gains),"gains":gains}
