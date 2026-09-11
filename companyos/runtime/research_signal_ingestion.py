from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class ResearchSignalRecord:
    signal_id: str
    opportunity_id: str
    source_type: str
    source_name: str
    title: str
    content: str
    url_or_ref: str
    published_at_unix: float | None
    ingested_at_unix: float
    source_quality: float
    relevance_hint: float
    dedupe_key: str
    metadata: dict[str, Any]


class ResearchSignalStore:
    """
    Persistent intake store for research/news/market/product signals.

    Phase 108 does not fetch the internet itself. It accepts signals from
    future connectors, tools, agents, or manual imports.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".companyos_runtime" / "research_signals")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, signal_id: str) -> Path:
        return self.root / f"{signal_id}.json"

    def save(self, record: ResearchSignalRecord) -> None:
        path = self._path(record.signal_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(asdict(record), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    def load(self, signal_id: str) -> ResearchSignalRecord:
        return ResearchSignalRecord(**json.loads(self._path(signal_id).read_text()))

    def all_records(self) -> list[ResearchSignalRecord]:
        out = []
        for p in self.root.glob("*.json"):
            try:
                out.append(self.load(p.stem))
            except Exception:
                continue
        return out

    @staticmethod
    def dedupe_key(
        *,
        opportunity_id: str,
        source_name: str,
        title: str,
        content: str,
        url_or_ref: str,
    ) -> str:
        normalized = "|".join([
            opportunity_id.strip().lower(),
            source_name.strip().lower(),
            " ".join(title.lower().split()),
            " ".join(content.lower().split())[:1000],
            url_or_ref.strip().lower(),
        ])
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def find_by_dedupe_key(self, key: str) -> ResearchSignalRecord | None:
        for record in self.all_records():
            if record.dedupe_key == key:
                return record
        return None

    def ingest(
        self,
        *,
        opportunity_id: str,
        source_type: str,
        source_name: str,
        title: str,
        content: str,
        url_or_ref: str = "",
        published_at_unix: float | None = None,
        source_quality: float = 0.5,
        relevance_hint: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> ResearchSignalRecord:
        key = self.dedupe_key(
            opportunity_id=opportunity_id,
            source_name=source_name,
            title=title,
            content=content,
            url_or_ref=url_or_ref,
        )
        existing = self.find_by_dedupe_key(key)
        if existing:
            return existing

        record = ResearchSignalRecord(
            signal_id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            source_type=(source_type or "unknown").strip().lower(),
            source_name=(source_name or "unknown").strip(),
            title=title.strip(),
            content=content.strip(),
            url_or_ref=url_or_ref.strip(),
            published_at_unix=published_at_unix,
            ingested_at_unix=time.time(),
            source_quality=max(0.0, min(1.0, float(source_quality))),
            relevance_hint=max(0.0, min(1.0, float(relevance_hint))),
            dedupe_key=key,
            metadata=dict(metadata or {}),
        )
        self.save(record)
        return record
