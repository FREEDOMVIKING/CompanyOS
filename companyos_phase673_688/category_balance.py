from collections import Counter

class CategoryBalance:
    """674: detect over-concentration by venture category."""

    def evaluate(self, ventures):
        counts = Counter(v.get("category","uncategorized") for v in ventures)
        total = max(1, len(ventures))
        shares = {k: round(v/total,4) for k,v in counts.items()}
        dominant = max(shares, key=shares.get) if shares else None
        return {
            "counts": dict(counts),
            "shares": shares,
            "dominant_category": dominant,
            "over_concentrated": bool(dominant and shares[dominant] > 0.6 and total >= 3),
        }
