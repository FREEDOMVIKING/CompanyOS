class HumanReviewGate:
    """882: escalate stalled but non-dead opportunities for review."""
    def evaluate(self,convergence,confidence):
        stalled=convergence.get("decision")=="STALLED_REVISE"
        return {"required":stalled and float(confidence)>=0.45,
                "reason":"stalled_revalidation" if stalled else None}
