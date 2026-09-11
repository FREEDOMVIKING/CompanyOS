from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

from companyos.runtime.goal_lifecycle_manager import GoalLifecycleManager, GoalRecord


@dataclass
class GoalOutcomeEvaluation:
    goal_id: str
    evaluated_at_unix: float
    goal_state: str
    success: bool
    confidence: float
    outcome_summary: str
    next_action: str
    follow_up_goal: Optional[str]
    blocked_reason: Optional[str]
    evidence: list[dict[str, Any]]


class GoalOutcomeEvaluator:
    """
    Evaluates a completed/failed/blocked CEO-level goal and determines the
    next internal action.

    Phase 99 is deterministic and local. It does not perform external actions.
    """

    def __init__(
        self,
        lifecycle: GoalLifecycleManager | None = None,
        root: Path | None = None,
    ) -> None:
        self.lifecycle = lifecycle or GoalLifecycleManager()
        self.root = root or (Path.home() / ".companyos_runtime" / "goal_outcomes")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, goal_id: str) -> Path:
        return self.root / f"{goal_id}.json"

    def save(self, evaluation: GoalOutcomeEvaluation) -> None:
        path = self._path(evaluation.goal_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(asdict(evaluation), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    def evaluate(self, *, goal_id: str, goal: str = "") -> GoalOutcomeEvaluation:
        record: GoalRecord = self.lifecycle.refresh(goal_id=goal_id, goal=goal)

        evidence = []
        if isinstance(record.final_result, dict):
            for item in record.final_result.get("outputs", []):
                evidence.append({
                    "task_type": item.get("task_type"),
                    "agent": item.get("agent"),
                    "result": item.get("result"),
                })

        if record.state == "COMPLETED":
            evaluation = GoalOutcomeEvaluation(
                goal_id=goal_id,
                evaluated_at_unix=time.time(),
                goal_state=record.state,
                success=True,
                confidence=1.0 if evidence else 0.75,
                outcome_summary=f"Goal completed with {record.completed_tasks} completed tasks.",
                next_action="review_and_decide_follow_up",
                follow_up_goal=None,
                blocked_reason=None,
                evidence=evidence,
            )

        elif record.state == "FAILED":
            evaluation = GoalOutcomeEvaluation(
                goal_id=goal_id,
                evaluated_at_unix=time.time(),
                goal_state=record.state,
                success=False,
                confidence=1.0,
                outcome_summary=f"Goal failed after {record.failed_tasks} failed tasks.",
                next_action="diagnose_failure_and_retry_or_replan",
                follow_up_goal=f"Diagnose and recover goal: {record.goal}",
                blocked_reason=record.last_error,
                evidence=evidence,
            )

        elif record.state == "BLOCKED":
            evaluation = GoalOutcomeEvaluation(
                goal_id=goal_id,
                evaluated_at_unix=time.time(),
                goal_state=record.state,
                success=False,
                confidence=1.0,
                outcome_summary="Goal is blocked and cannot advance automatically.",
                next_action="resolve_dependency_or_replan",
                follow_up_goal=f"Resolve blockers for goal: {record.goal}",
                blocked_reason=record.last_error,
                evidence=evidence,
            )

        else:
            evaluation = GoalOutcomeEvaluation(
                goal_id=goal_id,
                evaluated_at_unix=time.time(),
                goal_state=record.state,
                success=False,
                confidence=0.5,
                outcome_summary="Goal is still in progress.",
                next_action="continue_execution",
                follow_up_goal=None,
                blocked_reason=None,
                evidence=evidence,
            )

        self.save(evaluation)
        return evaluation
