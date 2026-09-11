from __future__ import annotations

from typing import Any, Dict, List
import uuid
from .contracts import GoalRequest, TaskRecord

class ConservativeGoalPlanner:
    """
    Deterministic fallback planner.

    This deliberately creates internal planning/research/build-review tasks only.
    It never invents permission for external actions or financial broadcasts.
    """

    def decompose(self, goal: GoalRequest) -> List[TaskRecord]:
        objective = goal.objective.strip()

        specs = [
            ("research", "goal_research", {"objective": objective, "context": goal.context}),
            ("plan", "goal_plan", {"objective": objective, "context": goal.context}),
            ("build", "goal_build_internal", {"objective": objective, "context": goal.context}),
            ("review", "goal_review", {"objective": objective, "context": goal.context}),
        ]

        tasks = []
        for name, action, payload in specs:
            tasks.append(TaskRecord(
                task_id=str(uuid.uuid4()),
                goal_id=goal.goal_id,
                name=name,
                action=action,
                payload=payload,
            ))
        return tasks
