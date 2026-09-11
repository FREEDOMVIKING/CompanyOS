from companyos_phase301_320 import EvidenceStore
from .quality_pipeline import OpportunityQualityPipeline
from .quality_memory import QualityMemory

class CEOQualityBridge:
    """527: run quality intelligence over persistent evidence."""

    def __init__(self, root):
        self.store = EvidenceStore(root)
        self.pipeline = OpportunityQualityPipeline()
        self.memory = QualityMemory(root)

    def run(self, limit=500):
        records = self.store.read_recent(limit=limit)
        result = self.pipeline.run(records)
        for candidate in result.get("candidates",[])[:10]:
            self.memory.append(candidate)
        return result
