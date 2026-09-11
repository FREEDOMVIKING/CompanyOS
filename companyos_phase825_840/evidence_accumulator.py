from companyos_phase745_760 import DedupeEvidence, ResearchNormalizer

class EvidenceAccumulator:
    """833: accumulate and normalize evidence across escalation rounds."""

    def merge(self, existing, new_items):
        merged = list(existing or []) + list(new_items or [])
        deduped = DedupeEvidence().dedupe(merged)
        return ResearchNormalizer().normalize(deduped)
