class FalsePositiveGuard:
    """848: prevent promotion on thin or one-sided evidence."""
    def evaluate(self, packet):
        evidence=list((packet or {}).get("evidence") or [])
        source_classes={e.get("source_class","unknown") for e in evidence}
        confidence=float((packet or {}).get("confidence",0) or 0)
        flags=[]
        if len(evidence)<3: flags.append("too_little_evidence")
        if len(source_classes)<2: flags.append("insufficient_source_diversity")
        if confidence<0.6: flags.append("low_research_confidence")
        return {"passed":not flags,"flags":flags}
