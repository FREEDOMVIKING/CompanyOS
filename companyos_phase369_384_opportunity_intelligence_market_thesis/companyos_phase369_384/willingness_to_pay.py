from __future__ import annotations

class WillingnessToPay:
    """375: infer WTP signals from spend, pricing, labor, and revenue impact."""

    TERMS = ("price","pricing","expensive","subscription","cost","pay","revenue","labor","hours")

    def score(self, cluster):
        text = " ".join(
            f"{r.get('title','')} {r.get('text','')}"
            for r in cluster.get("records", [])
        ).lower()
        hits = sum(1 for t in self.TERMS if t in text)
        return min(10, 3 + hits)
