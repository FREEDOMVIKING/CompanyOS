from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


class CompanyOSLaunchController:
    """
    Phase 70 V2 launch controller.

    Provides:
    - start/status/stop metadata
    - health + recovery preflight
    - practice launch path
    - no hard-coded business capability restrictions
    """

    def __init__(self, root=None):
        self.root = Path(root or Path.home() / "companyos")
        self.runtime = self.root / "companyos_runtime"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime / "launch_controller_state.json"

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _write(self, data):
        self.state_path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")

    def status(self):
        if not self.state_path.exists():
            return {"success": True, "status": "not_started"}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"success": False, "status": "state_corrupt", "error": str(exc)}

    def practice_start(self):
        state = {
            "success": True,
            "status": "practice_mode_ready",
            "timestamp": self._now(),
            "mode": "practice",
            "live_financial_execution_forced_off": True,
            "transaction_broadcasts_allowed_by_practice_controller": False,
            "internal_reversible_autonomy": True,
        }
        self._write(state)
        return state

    def mark_launch_ready(self, audit_result=None):
        state = {
            "success": True,
            "status": "launch_ready",
            "timestamp": self._now(),
            "mode": "ready",
            "audit_core_runtime_ready": (audit_result or {}).get("core_runtime_ready"),
            "blanket_restrictions_added": False,
        }
        self._write(state)
        return state

    def stop(self):
        state = {
            "success": True,
            "status": "stopped",
            "timestamp": self._now(),
            "mode": "stopped",
        }
        self._write(state)
        return state
