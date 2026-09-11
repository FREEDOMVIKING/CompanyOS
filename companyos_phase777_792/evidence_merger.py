from companyos_phase745_760 import DedupeEvidence
class EvidenceMerger:
    """782: merge and deduplicate evidence across providers."""
    def merge(self, batches):
        merged=[]
        for batch in batches or []:
            merged.extend(batch.get("items",[]))
        return DedupeEvidence().dedupe(merged)
