class ProblemEvidenceScore:
    """845: score customer/problem evidence strength."""
    def score(self, packet):
        evidence=list((packet or {}).get("evidence") or [])
        problem=sum(1 for e in evidence if "problem" in e.get("tags",[]))
        demand=sum(1 for e in evidence if "demand" in e.get("tags",[]))
        total=max(1,len(evidence))
        score=min(1.0, ((problem*0.6)+(demand*0.4))/total)
        return round(score,3)
