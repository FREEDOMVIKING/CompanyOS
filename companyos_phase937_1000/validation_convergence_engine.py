class ValidationConvergenceEngine:
    """953-960: decide GO/REVISE/KILL/HUMAN_REVIEW from rescored evidence."""
    def decide(self, validation, history=None, max_rounds_reached=False):
        scores = dict((validation or {}).get("scores") or {})
        c = float(scores.get("validation_confidence",0))
        fp = bool((validation or {}).get("false_positive_guard",{}).get("passed",True))
        contradictions = bool((validation or {}).get("contradictions",{}).get("resolved",True))

        if fp and contradictions and c >= 0.72:
            return {"decision":"GO","reason":"validated_opportunity"}
        if c < 0.40:
            return {"decision":"KILL","reason":"insufficient_evidence_strength"}

        hist = list(history or [])
        if len(hist) >= 2:
            a=float(hist[-2].get("confidence",0))
            b=float(hist[-1].get("confidence",0))
            if abs(b-a) < 0.015 and max_rounds_reached:
                return {"decision":"HUMAN_REVIEW","reason":"confidence_plateau"}

        if max_rounds_reached:
            return {"decision":"HUMAN_REVIEW","reason":"bounded_validation_exhausted"}
        return {"decision":"REVISE","reason":"more_evidence_required"}
