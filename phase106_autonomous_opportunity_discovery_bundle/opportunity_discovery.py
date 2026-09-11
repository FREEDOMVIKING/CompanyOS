from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


@dataclass
class OpportunityRecord:
    opportunity_id: str
    title: str
    description: str
    source: str
    category: str
    score: float
    confidence: float
    novelty: float
    feasibility: float
    strategic_fit: float
    expected_value: float
    requires_external_action: bool
    requires_financial_action: bool
    created_at_unix: float
    updated_at_unix: float
    dedupe_key: str
    metadata: dict[str, Any]


class OpportunityDiscoveryStore:
    """
    Persistent local store for candidate opportunities.

    Phase 106 is an INTERNAL discovery layer. It does not browse by itself,
    perform external actions, sign transactions, or broadcast transactions.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".companyos_runtime" / "opportunities")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, opportunity_id: str) -> Path:
        return self.root / f"{opportunity_id}.json"

    def save(self, record: OpportunityRecord) -> None:
        path = self._path(record.opportunity_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(asdict(record), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    def load(self, opportunity_id: str) -> OpportunityRecord:
        data = json.loads(self._path(opportunity_id).read_text(encoding="utf-8"))
        return OpportunityRecord(**data)

    def all_records(self) -> list[OpportunityRecord]:
        records = []
        for p in self.root.glob("*.json"):
            try:
                records.append(self.load(p.stem))
            except Exception:
                continue
        return records

    def find_by_dedupe_key(self, dedupe_key: str) -> OpportunityRecord | None:
        for record in self.all_records():
            if record.dedupe_key == dedupe_key:
                return record
        return None

    @staticmethod
    def make_dedupe_key(title: str, description: str, category: str) -> str:
        normalized = "|".join([
            " ".join(title.lower().split()),
            " ".join(description.lower().split()),
            " ".join(category.lower().split()),
        ])
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def upsert_candidate(
        self,
        *,
        title: str,
        description: str,
        source: str,
        category: str = "general",
        confidence: float = 0.5,
        novelty: float = 0.5,
        feasibility: float = 0.5,
        strategic_fit: float = 0.5,
        expected_value: float = 0.5,
        requires_external_action: bool = False,
        requires_financial_action: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> OpportunityRecord:
        dedupe_key = self.make_dedupe_key(title, description, category)
        existing = self.find_by_dedupe_key(dedupe_key)

        score = round(
            (
                max(0.0, min(1.0, confidence)) * 0.20
                + max(0.0, min(1.0, novelty)) * 0.15
                + max(0.0, min(1.0, feasibility)) * 0.25
                + max(0.0, min(1.0, strategic_fit)) * 0.20
                + max(0.0, min(1.0, expected_value)) * 0.20
            ) * 100.0,
            4,
        )

        now = time.time()

        if existing:
            existing.updated_at_unix = now
            existing.score = score
            existing.confidence = confidence
            existing.novelty = novelty
            existing.feasibility = feasibility
            existing.strategic_fit = strategic_fit
            existing.expected_value = expected_value
            existing.requires_external_action = requires_external_action
            existing.requires_financial_action = requires_financial_action
            existing.metadata.update(metadata or {})
            self.save(existing)
            return existing

        record = OpportunityRecord(
            opportunity_id=str(uuid.uuid4()),
            title=title.strip(),
            description=description.strip(),
            source=source.strip() or "unknown",
            category=category.strip() or "general",
            score=score,
            confidence=float(confidence),
            novelty=float(novelty),
            feasibility=float(feasibility),
            strategic_fit=float(strategic_fit),
            expected_value=float(expected_value),
            requires_external_action=bool(requires_external_action),
            requires_financial_action=bool(requires_financial_action),
            created_at_unix=now,
            updated_at_unix=now,
            dedupe_key=dedupe_key,
            metadata=dict(metadata or {}),
        )
        self.save(record)
        return record
