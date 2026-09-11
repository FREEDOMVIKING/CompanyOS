class CommercialIntent:
    """516: score signals indicating willingness to buy, replace, or pay."""

    TERMS = {
        "pay":2.0, "pricing":1.5, "price":1.0, "expensive":1.0,
        "subscription":1.0, "budget":1.5, "buy":2.0, "purchase":2.0,
        "replace":1.5, "revenue":1.0, "customer":0.5
    }

    def score(self, record):
        text = f"{record.get('title','')} {record.get('text','')}".lower()
        score = sum(weight for term, weight in self.TERMS.items() if term in text)
        return round(min(10, score), 2)
