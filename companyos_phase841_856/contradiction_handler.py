class ContradictionHandler:
    """849: penalize unresolved contradictions."""
    def evaluate(self, packet):
        topics=list(((packet or {}).get("contradictions") or {}).get("topics",[]) or [])
        penalty=min(0.3, len(topics)*0.1)
        return {"topics":topics,"penalty":round(penalty,3),"resolved":len(topics)==0}
