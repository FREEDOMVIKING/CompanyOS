from __future__ import annotations

from dataclasses import dataclass

from companyos.runtime.research_signal_ingestion import ResearchSignalStore
from companyos.runtime.research_signal_normalizer import ResearchSignalNormalizer
from companyos.runtime.opportunity_research_bridge import OpportunityResearchBridge


@dataclass(frozen=True)
class ResearchSignalPipelineResult:
    signal_id: str
    evidence_id: str
    opportunity_id: str
    direction: str
    research_decision: str
    score_before: float
    score_after: float


class ResearchSignalPipeline:
    """
    End-to-end Phase 108 path:
    raw signal -> normalized evidence -> Phase 107 assessment -> opportunity rescore
    """

    def __init__(self) -> None:
        self.signal_store = ResearchSignalStore()
        self.normalizer = ResearchSignalNormalizer()
        self.bridge = OpportunityResearchBridge()

    def process(
        self,
        *,
        opportunity_id: str,
        source_type: str,
        source_name: str,
        title: str,
        content: str,
        url_or_ref: str = "",
        source_quality: float = 0.5,
        relevance_hint: float = 0.5,
    ) -> ResearchSignalPipelineResult:
        signal = self.signal_store.ingest(
            opportunity_id=opportunity_id,
            source_type=source_type,
            source_name=source_name,
            title=title,
            content=content,
            url_or_ref=url_or_ref,
            source_quality=source_quality,
            relevance_hint=relevance_hint,
        )

        normalized = self.normalizer.normalize(signal)
        decision = self.bridge.apply(opportunity_id)

        return ResearchSignalPipelineResult(
            signal_id=signal.signal_id,
            evidence_id=normalized.evidence_id,
            opportunity_id=opportunity_id,
            direction=normalized.direction,
            research_decision=decision.decision,
            score_before=decision.score_before,
            score_after=decision.score_after,
        )
