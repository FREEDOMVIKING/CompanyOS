from __future__ import annotations
from typing import Any, Dict, List

class MarketFeedbackEngine:
    """Phase 65: convert customer/market signals into structured evidence."""
    def summarize(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not signals:
            return {"count": 0, "sentiment": 0.0, "demand_signal": 0.0, "themes": []}
        sentiment = sum(float(s.get("sentiment", 0)) for s in signals) / len(signals)
        demand = sum(float(s.get("demand", 0)) for s in signals) / len(signals)
        themes = []
        for s in signals:
            theme = s.get("theme")
            if theme and theme not in themes:
                themes.append(theme)
        return {
            "count": len(signals),
            "sentiment": round(sentiment, 4),
            "demand_signal": round(demand, 4),
            "themes": themes[:20],
        }
