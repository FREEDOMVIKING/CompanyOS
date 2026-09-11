class ConvergenceTracker:
    """879: track validation confidence/decision history."""
    def append(self,history,validation):
        h=list(history or [])
        h.append({"confidence":float((validation.get("scores") or {}).get("validation_confidence",0)),
                  "decision":validation.get("decision")})
        return h
