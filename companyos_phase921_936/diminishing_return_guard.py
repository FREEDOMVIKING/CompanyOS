class DiminishingReturnGuard:
    """930: stop spending research attempts when novelty and confidence gains both collapse."""
    def evaluate(self, rounds, gain_threshold=0.02, novelty_threshold=0.25, window=2):
        r=list(rounds or [])[-window:]
        if len(r)<window:return {"stop":False,"reason":"insufficient_history"}
        low=all(float(x.get("confidence_delta",0))<gain_threshold and float(x.get("novelty",0))<novelty_threshold for x in r)
        return {"stop":low,"reason":"diminishing_returns" if low else "continue"}
