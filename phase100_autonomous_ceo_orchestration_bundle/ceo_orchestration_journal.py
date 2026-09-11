from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class CEOOrchestrationJournal:
    """Append-only JSONL journal for CEO orchestration events."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (
            Path.home() / ".companyos_runtime" / "ceo_orchestration_journal.jsonl"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        orchestration_id: str,
        event: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        row = {
            "timestamp_unix": time.time(),
            "orchestration_id": orchestration_id,
            "event": event,
            "payload": payload or {},
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")
