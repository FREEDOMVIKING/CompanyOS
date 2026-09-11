from __future__ import annotations
from companyos_phase321_336 import EvidenceQuality

class ResearchQualityGate:
    """341: retain evidence meeting a minimum quality threshold."""

    def __init__(self, min_score=5):
        self.min_score = int(min_score)
        self.scorer = EvidenceQuality()

    def apply(self, records):
        accepted, rejected = [], []
        for record in records:
            score = self.scorer.score(record)
            item = {**record, "quality_score": score}
            (accepted if score >= self.min_score else rejected).append(item)
        return {"accepted": accepted, "rejected": rejected}
