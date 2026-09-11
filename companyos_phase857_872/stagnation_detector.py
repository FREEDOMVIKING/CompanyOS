class StagnationDetector:
    def evaluate(self,deltas,min_delta=0.02,window=2):
        recent=list(deltas or [])[-window:]
        stagnant=len(recent)>=window and all(float(x.get("delta",0))<min_delta for x in recent)
        return {"stagnant":stagnant,"window":window,"min_delta":min_delta}
