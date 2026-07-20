from __future__ import annotations
from typing import Any, Dict, List

class OpportunityHunter:
    """133: continuously rank opportunity signals for autonomous investigation."""

    def discover(self, signals: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        out = []
        for s in signals:
            demand = float(s.get("demand", 0))
            urgency = float(s.get("urgency", 0))
            willingness = float(s.get("willingness_to_pay", 0))
            competition = float(s.get("competition", 0))
            confidence = float(s.get("confidence", 0))
            score = (
                demand * 0.28
                + urgency * 0.20
                + willingness * 0.24
                + confidence * 0.18
                + (1 - competition) * 0.10
            )
            out.append({**s, "opportunity_score": round(score, 4)})
        out.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return out[:max(1, int(limit))]
