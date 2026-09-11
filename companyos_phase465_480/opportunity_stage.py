from companyos_phase369_384 import OpportunityIntelligenceCycle
from companyos_phase301_320 import EvidenceStore

class OpportunityStage:
    """470: run opportunity intelligence over collected evidence."""

    def __init__(self, root):
        self.store = EvidenceStore(root)
        self.engine = OpportunityIntelligenceCycle()

    def run(self, context=None):
        records = self.store.read_recent(limit=500)
        result = self.engine.run(records)
        return {
            "success": bool(result.get("market_theses")),
            "status": "opportunity_candidate_ready" if result.get("market_theses") else "no_opportunity_candidate",
            "stage":"opportunity",
            "data": {
                "top_thesis": result.get("top_thesis"),
                "market_theses": result.get("market_theses",[])[:5],
            }
        }
