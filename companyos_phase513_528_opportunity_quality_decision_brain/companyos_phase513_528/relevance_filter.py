class RelevanceFilter:
    """513: reject signals that are not plausibly tied to a business problem."""

    BUSINESS_TERMS = (
        "customer","business","workflow","software","tool","pricing","cost","manual",
        "slow","expensive","integration","support","sales","operations","reporting",
        "automation","subscription","revenue","billing","scheduling","compliance",
        "estimate","proposal","invoice","crm","api","developer","team","company"
    )

    NOISE_TERMS = (
        "archaeology","tomb","painting","celebrity","sports","movie review",
        "recipe","weather","politics only"
    )

    def score(self, record):
        text = f"{record.get('title','')} {record.get('text','')}".lower()
        business_hits = sum(1 for t in self.BUSINESS_TERMS if t in text)
        noise_hits = sum(1 for t in self.NOISE_TERMS if t in text)
        score = max(0, min(10, business_hits * 1.2 - noise_hits * 3))
        return round(score, 2)

    def apply(self, records, min_score=2.0):
        accepted, rejected = [], []
        for r in records:
            s = self.score(r)
            item = {**r, "relevance_score": s}
            (accepted if s >= min_score else rejected).append(item)
        return {"accepted": accepted, "rejected": rejected}
