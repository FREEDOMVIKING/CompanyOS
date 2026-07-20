from __future__ import annotations
from typing import Any, Dict

class HealthSupervisor:
    """Phase 58: system health rollup and escalation."""
    def evaluate(self, checks: Dict[str, bool]) -> Dict[str, Any]:
        total = len(checks)
        passed = sum(1 for v in checks.values() if bool(v))
        ratio = passed / total if total else 1.0
        return {
            "healthy": ratio >= 0.8,
            "score": round(ratio, 4),
            "passed": passed,
            "total": total,
            "failed_checks": [k for k, v in checks.items() if not v],
            "status": "healthy" if ratio >= 0.8 else "degraded" if ratio >= 0.5 else "critical",
        }
