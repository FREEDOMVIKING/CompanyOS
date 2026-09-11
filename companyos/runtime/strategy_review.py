from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class StrategyReview:
    continue_project: bool
    reason: str
    score: float

class StrategyReviewer:
    def review(self, opportunity_score, qa_passed, blocked, expected_margin):
        score=float(opportunity_score)*0.4 + (100 if qa_passed else 0)*0.25 + (0 if blocked else 100)*0.15 + max(0,min(100,float(expected_margin)*100))*0.2
        return StrategyReview(score>=60,"continue" if score>=60 else "reconsider",round(score,2))
