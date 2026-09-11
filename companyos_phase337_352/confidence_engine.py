from __future__ import annotations

class OpportunityConfidence:
    """346: confidence score based on evidence quantity/quality/diversity."""

    def score(self, opportunity, source_count=1):
        evidence_count = len(opportunity.get("evidence", []))
        pain_count = int((opportunity.get("gap") or {}).get("pain_evidence_count", 0))
        score = min(1.0, 0.15 + evidence_count*0.08 + pain_count*0.10 + min(source_count,5)*0.07)
        return round(score, 3)
