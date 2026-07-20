from __future__ import annotations
from typing import Any, Dict, List

class ObjectiveManager:
    """Phase 61: normalize, prioritize, and track strategic objectives."""
    def prioritize(self, objectives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ranked = []
        for obj in objectives:
            impact = max(0.0, float(obj.get("impact", 0)))
            urgency = max(0.0, float(obj.get("urgency", 0)))
            confidence = max(0.0, min(1.0, float(obj.get("confidence", 0.5))))
            effort = max(1.0, float(obj.get("effort", 1)))
            score = (impact * 0.45 + urgency * 0.35 + confidence * 20.0 * 0.20) / effort
            ranked.append({**obj, "priority_score": round(score, 4)})
        return sorted(ranked, key=lambda x: x["priority_score"], reverse=True)
