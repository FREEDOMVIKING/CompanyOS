from __future__ import annotations

class NoiseFilter:
    """369: reject weak/non-business signals before thesis generation."""

    BAD_TERMS = (
        "tomb of", "painting", "celebrity", "sports score", "movie review",
        "weather only", "random trivia"
    )

    BUSINESS_TERMS = (
        "manual", "workflow", "pricing", "subscription", "customer", "business",
        "integration", "software", "tool", "cost", "expensive", "slow",
        "repetitive", "operations", "invoice", "sales", "support", "reporting",
        "estimate", "proposal", "compliance", "scheduling"
    )

    def keep(self, record):
        text = f"{record.get('title','')} {record.get('text','')}".lower()
        if any(term in text for term in self.BAD_TERMS):
            return False
        return any(term in text for term in self.BUSINESS_TERMS)

    def apply(self, records):
        accepted, rejected = [], []
        for r in records:
            (accepted if self.keep(r) else rejected).append(r)
        return {"accepted": accepted, "rejected": rejected}
