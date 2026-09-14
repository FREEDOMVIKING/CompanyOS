from __future__ import annotations

import json
import time
from pathlib import Path

from companyos.runtime.runtime_control import UnifiedRuntimeControl


class RuntimeStatus:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.control = UnifiedRuntimeControl(self.root)

    def _read(self, name: str):
        path = self.runtime_root / name
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}

    def status(self):
        health = self.control.health()
        return {
            "success": bool(health.get("healthy")),
            "status": "healthy" if health.get("healthy") else "degraded",
            "checked_at_unix": time.time(),
            "continuous_runtime": health,
            "continuous_goal_runtime": self._read(
                "continuous_goal_runtime_state.json"
            ),
            "productive_autonomy_watchdog": self._read(
                "productive_autonomy_watchdog_state.json"
            ),
        }
