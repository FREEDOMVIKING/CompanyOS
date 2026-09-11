from __future__ import annotations

class CrossSourceAgreement:
    """371: confidence boost when independent sources point to same pain."""

    def score(self, cluster):
        sources = {r.get("source") for r in cluster.get("records", []) if r.get("source")}
        count = len(sources)
        if count >= 4:
            level = "strong"
        elif count >= 2:
            level = "moderate"
        else:
            level = "weak"
        return {"source_count": count, "agreement": level, "score": min(1.0, 0.25 + count*0.2)}
