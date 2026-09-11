class EvidenceConfidence:
    """757: aggregate evidence confidence."""
    def score(self, evidence):
        vals=[float(x.get("evidence_score",0)) for x in evidence or []]
        if not vals: return 0.0
        vals=sorted(vals, reverse=True)[:10]
        return round(sum(vals)/len(vals),3)
