from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class BusinessObjective:
    objective_id: str
    title: str
    target_metric: str
    target_value: float
    timeframe_days: int
    priority: int
    metadata: dict[str, Any]

class BusinessObjectiveEngine:
    def build(self, *, objective_id, title, target_metric, target_value, timeframe_days=30, priority=100, metadata=None):
        return BusinessObjective(
            objective_id=str(objective_id),
            title=str(title).strip(),
            target_metric=str(target_metric).strip(),
            target_value=float(target_value),
            timeframe_days=max(1, int(timeframe_days)),
            priority=int(priority),
            metadata=dict(metadata or {}),
        )
