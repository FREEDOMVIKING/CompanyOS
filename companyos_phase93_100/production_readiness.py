from __future__ import annotations
from typing import Any, Dict

class ProductionReadiness:
    """97: production-readiness gate for reliability and governance."""
    MINIMUMS = {
        "tests": 1.0,
        "monitoring": 0.8,
        "rollback": 1.0,
        "security": 0.8,
        "observability": 0.8,
    }

    def evaluate(self, checks: Dict[str, Any]) -> Dict[str, Any]:
        detail = {}
        for key, minimum in self.MINIMUMS.items():
            value = float(checks.get(key, 0))
            detail[key] = {"value": value, "minimum": minimum, "passed": value >= minimum}
        return {"ready": all(x["passed"] for x in detail.values()), "checks": detail}
