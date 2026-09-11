from __future__ import annotations

from dataclasses import dataclass

from companyos.runtime.research_signal_ingestion import ResearchSignalRecord
from companyos.runtime.research_evidence_pipeline import ResearchEvidenceStore


@dataclass(frozen=True)
class SignalNormalizationResult:
    signal_id: str
    opportunity_id: str
    evidence_id: str
    direction: str
    confidence: float
    quality: float
    relevance: float


class ResearchSignalNormalizer:
    """
    Converts ingested raw signals into Phase 107 evidence records.

    Deterministic heuristic classification for Phase 108.
    Future phases can swap in richer research/LLM classifiers.
    """

    POSITIVE_MARKERS = (
        "growth",
        "demand",
        "adoption",
        "profitable",
        "revenue",
        "opportunity",
        "feasible",
        "underserved",
        "increasing",
        "strong interest",
    )

    NEGATIVE_MARKERS = (
        "decline",
        "shrinking",
        "unprofitable",
        "saturated",
        "regulatory risk",
        "low demand",
        "high churn",
        "fraud",
        "unsafe",
        "blocked",
    )

    def __init__(self, evidence_store: ResearchEvidenceStore | None = None) -> None:
        self.evidence_store = evidence_store or ResearchEvidenceStore()

    def classify_direction(self, text: str) -> str:
        lowered = text.lower()
        pos = sum(1 for marker in self.POSITIVE_MARKERS if marker in lowered)
        neg = sum(1 for marker in self.NEGATIVE_MARKERS if marker in lowered)

        if pos > neg:
            return "support"
        if neg > pos:
            return "contradict"
        return "neutral"

    def normalize(self, signal: ResearchSignalRecord) -> SignalNormalizationResult:
        text = f"{signal.title}. {signal.content}".strip()
        direction = self.classify_direction(text)

        confidence = min(
            1.0,
            max(
                0.25,
                (signal.source_quality * 0.55)
                + (signal.relevance_hint * 0.45),
            ),
        )

        evidence = self.evidence_store.add(
            opportunity_id=signal.opportunity_id,
            source=f"{signal.source_type}:{signal.source_name}",
            claim=text[:2000],
            direction=direction,
            confidence=confidence,
            quality=signal.source_quality,
            relevance=signal.relevance_hint,
            metadata={
                "signal_id": signal.signal_id,
                "url_or_ref": signal.url_or_ref,
                "published_at_unix": signal.published_at_unix,
            },
        )

        return SignalNormalizationResult(
            signal_id=signal.signal_id,
            opportunity_id=signal.opportunity_id,
            evidence_id=evidence.evidence_id,
            direction=direction,
            confidence=confidence,
            quality=signal.source_quality,
            relevance=signal.relevance_hint,
        )
