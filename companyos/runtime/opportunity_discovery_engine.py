from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Any

from companyos.runtime.opportunity_discovery import OpportunityDiscoveryStore, OpportunityRecord


@dataclass(frozen=True)
class DiscoveryBatchResult:
    discovered: int
    stored: int
    top_opportunity_id: str | None
    top_score: float


class OpportunityDiscoveryEngine:
    """
    Deterministic Phase 106 discovery adapter.

    Accepts candidate signals from future connectors/agents and converts them
    into scored persistent opportunities. It does not fetch external data itself.
    """

    def __init__(self, store: OpportunityDiscoveryStore | None = None) -> None:
        self.store = store or OpportunityDiscoveryStore()

    def ingest_candidates(self, candidates: Iterable[dict[str, Any]]) -> DiscoveryBatchResult:
        stored: list[OpportunityRecord] = []

        count = 0
        for item in candidates:
            count += 1
            title = str(item.get("title", "")).strip()
            description = str(item.get("description", "")).strip()
            if not title or not description:
                continue

            record = self.store.upsert_candidate(
                title=title,
                description=description,
                source=str(item.get("source", "unknown")),
                category=str(item.get("category", "general")),
                confidence=float(item.get("confidence", 0.5)),
                novelty=float(item.get("novelty", 0.5)),
                feasibility=float(item.get("feasibility", 0.5)),
                strategic_fit=float(item.get("strategic_fit", 0.5)),
                expected_value=float(item.get("expected_value", 0.5)),
                requires_external_action=bool(item.get("requires_external_action", False)),
                requires_financial_action=bool(item.get("requires_financial_action", False)),
                metadata=dict(item.get("metadata", {})),
            )
            stored.append(record)

        top = max(stored, key=lambda x: x.score) if stored else None

        return DiscoveryBatchResult(
            discovered=count,
            stored=len(stored),
            top_opportunity_id=top.opportunity_id if top else None,
            top_score=top.score if top else 0.0,
        )
