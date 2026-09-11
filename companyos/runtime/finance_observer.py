from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class FinanceSnapshot:
    revenue: float
    cost: float
    profit: float
    margin: float

class FinanceObserver:
    def snapshot(self,revenue,cost):
        revenue=float(revenue); cost=float(cost)
        profit=revenue-cost
        margin=(profit/revenue) if revenue else 0.0
        return FinanceSnapshot(revenue,cost,profit,margin)
