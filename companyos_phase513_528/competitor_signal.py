class CompetitorSignal:
    """519: summarize evidence of existing spend and replacement opportunity."""

    TERMS = ("competitor","alternative","existing software","subscription","pricing","replace","switch")

    def analyze(self, record):
        text = f"{record.get('title','')} {record.get('text','')}".lower()
        hits = [x for x in self.TERMS if x in text]
        return {
            "signals": hits,
            "has_competitive_market": bool(hits),
            "replacement_opportunity": any(x in hits for x in ("replace","switch","existing software")),
        }
