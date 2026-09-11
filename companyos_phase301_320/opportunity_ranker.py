from __future__ import annotations
from companyos_phase293_300 import OpportunityPipeline

class OpportunityRanker:
    """311: reuse Phase 293-300 economics + validation ranking."""

    def __init__(self):
        self.pipeline = OpportunityPipeline()

    def rank(self, opportunities):
        return self.pipeline.rank(opportunities)
