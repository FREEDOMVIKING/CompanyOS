class WeakSignalFilter:
    """754: remove low-confidence, low-credibility evidence."""
    def filter(self, evidence, min_score=0.4):
        kept=[]; dropped=[]
        for item in evidence or []:
            score=float(item.get("evidence_score",0))
            (kept if score >= min_score else dropped).append(item)
        return {"kept":kept,"dropped":dropped}
