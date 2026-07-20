from __future__ import annotations
from typing import Any, Dict

class ExperimentEngine:
    """Phase 64: define measurable experiments before scaling decisions."""
    def design(self, hypothesis: str, metric: str, baseline: float, target: float, max_cost: float) -> Dict[str, Any]:
        return {
            "hypothesis": hypothesis,
            "metric": metric,
            "baseline": float(baseline),
            "target": float(target),
            "max_cost": max(0.0, float(max_cost)),
            "success_condition": f"{metric} >= {float(target)}",
            "status": "planned",
        }

    def evaluate(self, experiment: Dict[str, Any], observed: float) -> Dict[str, Any]:
        target = float(experiment.get("target", 0))
        observed = float(observed)
        return {
            "success": observed >= target,
            "observed": observed,
            "target": target,
            "recommendation": "consider_scale" if observed >= target else "iterate_or_stop",
        }
