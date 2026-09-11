from companyos_phase745_760 import EvidenceConfidence

class ConfidenceProgress:
    """834: track confidence changes across rounds."""

    def evaluate(self, before_evidence, after_evidence):
        before = EvidenceConfidence().score(before_evidence or [])
        after = EvidenceConfidence().score(after_evidence or [])
        return {
            "before": before,
            "after": after,
            "delta": round(after - before, 3),
            "improved": after > before,
        }
