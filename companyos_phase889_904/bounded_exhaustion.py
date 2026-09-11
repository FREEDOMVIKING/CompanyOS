class BoundedExhaustionPolicy:
    """897: choose review vs archive after bounded autonomous attempts."""
    def decide(self,confidence):
        c=float(confidence)
        if c<0.45: return {"action":"archive","reason":"low_confidence_after_max_rounds"}
        return {"action":"review","reason":"uncertain_after_max_rounds"}
