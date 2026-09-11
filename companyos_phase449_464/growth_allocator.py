class GrowthAllocator:
    """458: allocate attention to the strongest growth experiments."""

    def rank(self, experiments):
        ranked = []
        for e in experiments:
            impact = float(e.get("expected_impact",0))
            confidence = float(e.get("confidence",0))
            effort = max(1.0, float(e.get("effort",1)))
            score = (impact * confidence) / effort
            ranked.append({**e, "allocation_score":round(score,3)})
        return sorted(ranked, key=lambda x:x["allocation_score"], reverse=True)
