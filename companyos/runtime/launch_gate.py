from __future__ import annotations

from pathlib import Path
from companyos.runtime.launch_readiness import LaunchReadinessAudit


class LaunchGate:
    def __init__(self, root: Path | None = None):
        self.audit = LaunchReadinessAudit(root)

    def evaluate(self):
        audit = self.audit.run()
        return {
            "allowed": bool(audit.get("ready")),
            "reason": "launch_readiness_passed"
            if audit.get("ready")
            else "launch_readiness_blocked",
            "audit": audit,
        }
