from __future__ import annotations
from typing import Any, Dict, Iterable, List

class PortfolioManager:
    """Phase 57: rank and rebalance internal ventures by evidence-adjusted value."""
    def rank(self, ventures: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for v in ventures:
            expected = float(v.get("expected_value", 0))
            confidence = max(0.0, min(1.0, float(v.get("confidence", 0.5))))
            risk = max(0.0, min(1.0, float(v.get("risk", 0.5))))
            score = expected * confidence * (1.0 - 0.7 * risk)
            out.append({**v, "portfolio_score": round(score, 4)})
        return sorted(out, key=lambda x: x["portfolio_score"], reverse=True)
