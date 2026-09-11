from __future__ import annotations

class CustomerPainFilter:
    """357: identify records likely to describe actionable customer pain."""

    TERMS = (
        "manual","slow","expensive","difficult","frustrat","time consuming",
        "time-consuming","missing feature","pain","problem","broken","error",
        "integration","workflow","repetitive","cost"
    )

    def apply(self, records):
        out = []
        for r in records:
            text = f"{r.get('title','')} {r.get('text','')}".lower()
            matches = [term for term in self.TERMS if term in text]
            if matches:
                out.append({**r, "pain_terms": matches})
        return out
