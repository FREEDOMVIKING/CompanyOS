class OpportunityQuality:
    """521: aggregate candidate quality from evidence dimensions."""

    def score(self, candidate):
        dims = candidate.get("dimensions") or {}
        weights = {
            "relevance":0.20,
            "evidence":0.15,
            "pain":0.20,
            "commercial_intent":0.15,
            "market_plausibility":0.15,
            "cross_source":0.15,
        }
        total = 0.0
        for key, weight in weights.items():
            total += float(dims.get(key,0)) * weight
        return round(min(10, total), 2)
