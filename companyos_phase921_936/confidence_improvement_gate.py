class ConfidenceImprovementGate:
    """928: determine if adaptive research materially improved validation."""
    def evaluate(self,before,after,min_gain=0.02):
        b=float(before or 0); a=float(after or 0); d=round(a-b,3)
        return {"improved":d>=float(min_gain),"before":b,"after":a,"delta":d,"min_gain":min_gain}
