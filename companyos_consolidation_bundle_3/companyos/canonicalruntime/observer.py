from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import json, time

class RuntimeCycleObserver:
    def __init__(self, companyos_root: str | None = None):
        self.root = Path(companyos_root or (Path.home() / "companyos"))
        self.runtime = self.root / "companyos_runtime"
        self.out = self.runtime / "canonical_runtime"
        self.out.mkdir(parents=True, exist_ok=True)
        self.journal = self.out / "runtime_handoff.jsonl"

    def record(self, event: str, data: Dict[str, Any]) -> None:
        with self.journal.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.time(),
                "event": event,
                "data": data,
            }, sort_keys=True) + "\n")

    def phase102_status(self) -> Dict[str, Any]:
        candidates = [
            self.runtime / "unified_runtime_status.json",
            self.runtime / "autonomous_ceo_runtime_service.json",
            self.runtime / "ceo_runtime_status.json",
        ]
        found = []
        for p in candidates:
            if p.exists():
                try:
                    found.append({"path": str(p), "data": json.loads(p.read_text())})
                except Exception:
                    found.append({"path": str(p), "data": {}})
        return {
            "status_files_found": len(found),
            "files": found,
        }
