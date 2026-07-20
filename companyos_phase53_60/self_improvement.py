from __future__ import annotations
from typing import Any, Dict

class SelfImprovementEngine:
    """Phase 59: proposes bounded improvements without silently mutating core policy."""
    def propose(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        metric = str(observation.get("metric", "unknown"))
        actual = float(observation.get("actual", 0))
        target = float(observation.get("target", 0))
        gap = target - actual
        return {
            "metric": metric,
            "gap": round(gap, 4),
            "proposal": (
                f"Investigate and test an improvement for {metric}"
                if gap > 0 else f"Preserve current approach for {metric}"
            ),
            "auto_apply": False,
            "policy_mutation": False,
        }
