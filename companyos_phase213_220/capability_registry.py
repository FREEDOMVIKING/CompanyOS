from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class CapabilityRegistry:
    """218: persistent registry of verified self-built capabilities."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "capabilities.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def register(self, capability: str, record: Dict[str, Any]):
        data = self._read()
        data[capability] = record
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data[capability]

    def list(self):
        return self._read()
