class JunkRejector:
    """522: reject low-quality or weakly-supported opportunity candidates."""

    def decide(self, candidate):
        reasons = []
        if float(candidate.get("quality_score",0)) < 4.5:
            reasons.append("quality_below_threshold")
        if int(candidate.get("evidence_count",0)) < 2:
            reasons.append("insufficient_evidence")
        if int(candidate.get("source_count",0)) < 1:
            reasons.append("missing_source_diversity")
        return {"rejected": bool(reasons), "reasons": reasons}
