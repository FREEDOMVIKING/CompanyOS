class StagnationRootCause:
    """905: diagnose why revalidation confidence is not improving."""
    def analyze(self, history, validation, evidence=None):
        history=list(history or [])
        evidence=list(evidence or [])
        reasons=[]
        if len(history)>=2:
            a=float(history[-2].get("confidence",0))
            b=float(history[-1].get("confidence",0))
            if abs(b-a)<0.02:
                reasons.append("confidence_stagnation")
        scores=dict((validation or {}).get("scores") or {})
        if float(scores.get("problem_evidence",0))<0.65: reasons.append("weak_problem_evidence")
        if float(scores.get("pricing_validation",0))<0.60: reasons.append("weak_pricing_evidence")
        classes={e.get("source_class","unknown") for e in evidence if isinstance(e,dict)}
        if len(classes)<2: reasons.append("low_source_diversity")
        return {"reasons":reasons or ["unknown_stagnation"],"count":len(reasons)}
