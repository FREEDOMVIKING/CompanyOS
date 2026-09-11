class PainSignal:
    """517: score business pain severity and urgency."""

    TERMS = {
        "manual":1.0,"slow":1.0,"hours":1.5,"broken":2.0,"error":1.0,
        "difficult":1.0,"frustrating":1.0,"expensive":1.0,"repetitive":1.0,
        "urgent":2.0,"blocking":2.0,"cannot":1.5,"waste":1.5
    }

    def score(self, record):
        text = f"{record.get('title','')} {record.get('text','')}".lower()
        score = sum(weight for term, weight in self.TERMS.items() if term in text)
        return round(min(10, score), 2)
