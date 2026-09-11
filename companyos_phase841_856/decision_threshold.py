class DecisionThreshold:
    """851: GO / REVISE / KILL decision thresholds."""
    def decide(self, confidence, false_positive_passed, contradictions_resolved):
        c=float(confidence)
        if false_positive_passed and contradictions_resolved and c>=0.72:
            return {"decision":"GO","reason":"validation_threshold_met"}
        if c>=0.45:
            return {"decision":"REVISE","reason":"insufficient_validation_confidence"}
        return {"decision":"KILL","reason":"weak_or_invalid_opportunity"}
