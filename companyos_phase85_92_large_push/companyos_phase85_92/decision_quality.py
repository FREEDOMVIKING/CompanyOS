class DecisionQuality:
    """86: score decision quality before execution."""
    def score(self,decision):
        evidence=max(0,min(1,float(decision.get("evidence",0))))
        reversibility=max(0,min(1,float(decision.get("reversibility",0))))
        clarity=max(0,min(1,float(decision.get("clarity",0))))
        downside=max(0,min(1,float(decision.get("downside_risk",1))))
        score=evidence*.35+reversibility*.2+clarity*.25+(1-downside)*.2
        return {"quality_score":round(score,4),
        "recommendation":"proceed_to_gate" if score>=.7 else "gather_more_evidence" if score>=.45 else "do_not_execute"}
