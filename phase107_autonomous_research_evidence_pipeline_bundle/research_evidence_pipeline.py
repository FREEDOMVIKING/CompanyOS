from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class EvidenceRecord:
    evidence_id: str
    opportunity_id: str
    source: str
    claim: str
    direction: str
    confidence: float
    quality: float
    relevance: float
    created_at_unix: float
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ResearchAssessment:
    opportunity_id: str
    evidence_count: int
    support_score: float
    contradiction_score: float
    evidence_quality_score: float
    confidence_score: float
    decision: str
    reason: str


class ResearchEvidenceStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".companyos_runtime" / "research_evidence")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, evidence_id: str) -> Path:
        return self.root / f"{evidence_id}.json"

    def save(self, record: EvidenceRecord) -> None:
        path = self._path(record.evidence_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(asdict(record), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    def load(self, evidence_id: str) -> EvidenceRecord:
        return EvidenceRecord(**json.loads(self._path(evidence_id).read_text()))

    def all_for_opportunity(self, opportunity_id: str) -> list[EvidenceRecord]:
        out = []
        for p in self.root.glob("*.json"):
            try:
                rec = self.load(p.stem)
                if rec.opportunity_id == opportunity_id:
                    out.append(rec)
            except Exception:
                continue
        return out

    def add(
        self,
        *,
        opportunity_id: str,
        source: str,
        claim: str,
        direction: str,
        confidence: float,
        quality: float,
        relevance: float,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceRecord:
        direction = direction.lower().strip()
        if direction not in ("support", "contradict", "neutral"):
            raise ValueError("invalid_direction")

        record = EvidenceRecord(
            evidence_id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            source=source.strip() or "unknown",
            claim=claim.strip(),
            direction=direction,
            confidence=max(0.0, min(1.0, float(confidence))),
            quality=max(0.0, min(1.0, float(quality))),
            relevance=max(0.0, min(1.0, float(relevance))),
            created_at_unix=time.time(),
            metadata=dict(metadata or {}),
        )
        self.save(record)
        return record


class ResearchEvidenceEvaluator:
    def __init__(self, store: ResearchEvidenceStore | None = None) -> None:
        self.store = store or ResearchEvidenceStore()

    def assess(self, opportunity_id: str) -> ResearchAssessment:
        evidence = self.store.all_for_opportunity(opportunity_id)

        if not evidence:
            return ResearchAssessment(
                opportunity_id=opportunity_id,
                evidence_count=0,
                support_score=0.0,
                contradiction_score=0.0,
                evidence_quality_score=0.0,
                confidence_score=0.0,
                decision="needs_more_research",
                reason="no_evidence",
            )

        support = 0.0
        contradict = 0.0
        weighted_quality = 0.0
        weighted_conf = 0.0
        weight_total = 0.0

        for item in evidence:
            weight = item.quality * item.relevance
            weighted_quality += item.quality * item.relevance
            weighted_conf += item.confidence * weight
            weight_total += weight

            if item.direction == "support":
                support += item.confidence * weight
            elif item.direction == "contradict":
                contradict += item.confidence * weight

        quality_score = weighted_quality / max(1.0, len(evidence))
        confidence_score = weighted_conf / weight_total if weight_total > 0 else 0.0

        support_score = support / max(0.0001, support + contradict) if (support + contradict) > 0 else 0.5
        contradiction_score = 1.0 - support_score if (support + contradict) > 0 else 0.5

        if len(evidence) < 2 or quality_score < 0.45:
            decision = "needs_more_research"
            reason = "insufficient_evidence_quality"
        elif contradiction_score >= 0.55:
            decision = "reject_or_revise"
            reason = "contradictory_evidence_dominant"
        elif support_score >= 0.65 and confidence_score >= 0.60:
            decision = "advance"
            reason = "supporting_evidence_sufficient"
        else:
            decision = "hold"
            reason = "mixed_or_uncertain_evidence"

        return ResearchAssessment(
            opportunity_id=opportunity_id,
            evidence_count=len(evidence),
            support_score=round(support_score, 4),
            contradiction_score=round(contradiction_score, 4),
            evidence_quality_score=round(quality_score, 4),
            confidence_score=round(confidence_score, 4),
            decision=decision,
            reason=reason,
        )
