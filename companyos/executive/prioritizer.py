from typing import Dict, List
from .models import Venture


_STAGE_WEIGHT = {
    "discovery": 0.75,
    "validation": 0.90,
    "build": 1.00,
    "launch": 1.10,
    "operations": 1.05,
    "scale": 1.15,
    "paused": 0.25,
    "failed": 0.0,
}


def score_venture(v: Venture) -> float:
    upside = max(0.0, v.expected_return) * max(0.0, min(1.0, v.confidence))
    execution = (
        0.30 * max(0.0, min(1.0, v.urgency))
        + 0.35 * max(0.0, min(1.0, v.strategic_fit))
        + 0.20 * max(0.0, min(1.0, v.progress))
        + 0.15 * (0.0 if v.blocked else 1.0)
    )
    risk_penalty = (
        0.55 * max(0.0, min(1.0, v.risk))
        + 0.45 * max(0.0, min(1.0, v.failure_probability))
    )
    stage = _STAGE_WEIGHT.get(v.stage, 0.70)
    dependency_penalty = min(0.35, len(v.dependencies) * 0.05)
    return round(stage * (upside + execution) * (1.0 - min(0.9, risk_penalty + dependency_penalty)), 6)


def rank_ventures(ventures: List[Venture]) -> List[Dict]:
    ranked = [
        {
            "venture_id": v.venture_id,
            "name": v.name,
            "score": score_venture(v),
            "stage": v.stage,
            "blocked": v.blocked,
        }
        for v in ventures
    ]
    return sorted(ranked, key=lambda item: item["score"], reverse=True)
