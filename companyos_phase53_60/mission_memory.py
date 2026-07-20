from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

class MissionMemory:
    """Phase 53: persistent mission memory with bounded append-only records."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _read(self) -> List[Dict[str, Any]]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def append(self, record: Dict[str, Any], max_records: int = 1000) -> None:
        rows = self._read()
        rows.append(dict(record))
        rows = rows[-max(1, int(max_records)):]
        self.path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._read()[-max(1, int(limit)):]
