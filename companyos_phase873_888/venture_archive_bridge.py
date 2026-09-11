class VentureArchiveBridge:
    """883: archive only on explicit KILL or terminal low-confidence exhaustion."""
    def build(self,decision,confidence):
        archive=decision=="KILL" or (decision=="EXHAUSTED" and float(confidence)<0.45)
        return {"archive":archive,"reason":"validation_kill" if decision=="KILL" else ("low_confidence_exhausted" if archive else None)}
