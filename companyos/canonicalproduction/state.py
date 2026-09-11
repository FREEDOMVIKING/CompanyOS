from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import json, time

class ProductionStateStore:
    def __init__(self, runtime_root: Path):
        self.root = runtime_root / "canonical_production"
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_file = self.root / "state.json"
        self.journal = self.root / "journal.jsonl"

    def read(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text())
        except Exception:
            return {}

    def write(self, data: Dict[str, Any]) -> None:
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True))
        tmp.replace(self.state_file)

    def append(self, event: str, data: Dict[str, Any]) -> None:
        with self.journal.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.time(),
                "event": event,
                "data": data,
            }, sort_keys=True) + "\n")
