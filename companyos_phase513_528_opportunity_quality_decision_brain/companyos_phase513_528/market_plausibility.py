class MarketPlausibility:
    """518: infer whether a signal maps to a repeatable commercial segment."""

    SEGMENTS = {
        "contractor":2.0,"business":1.0,"team":1.0,"company":1.0,"developer":1.0,
        "agency":1.5,"clinic":1.5,"law firm":1.5,"accounting":1.5,"field service":1.5
    }

    def score(self, record):
        text = f"{record.get('title','')} {record.get('text','')}".lower()
        score = 2.0
        score += sum(weight for term, weight in self.SEGMENTS.items() if term in text)
        if any(x in text for x in ("workflow","software","operations","subscription","process")):
            score += 2.0
        return round(min(10, score), 2)
