from companyos_phase745_760 import EvidenceCompleteness

class EvidenceGapAnalyzer:
    """828: identify missing evidence dimensions."""

    def analyze(self, evidence):
        result = EvidenceCompleteness().evaluate(evidence or [])
        return {
            "missing": result.get("missing", []),
            "covered": result.get("covered", []),
            "complete": result.get("complete", False),
        }
