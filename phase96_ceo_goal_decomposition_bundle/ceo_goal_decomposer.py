from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue


@dataclass(frozen=True)
class GoalDecompositionResult:
    goal_id: str
    goal: str
    tasks_created: int
    task_ids: list[str]
    task_types: list[str]


class CEOGoalDecomposer:
    """
    Converts a high-level CEO goal into a small dependency-aware internal task plan.

    Phase 96 is deterministic and local:
    research -> planning -> build

    Later phases can replace the deterministic planner with adaptive/LLM planning
    while preserving the same durable queue contract.
    """

    def __init__(self, queue: AutonomousTaskQueue | None = None) -> None:
        self.queue = queue or AutonomousTaskQueue()

    def decompose(
        self,
        *,
        goal: str,
        priority_base: int = 100,
        goal_id: str | None = None,
    ) -> GoalDecompositionResult:
        goal = goal.strip()
        if not goal:
            raise ValueError("goal_empty")

        goal_id = goal_id or str(uuid.uuid4())

        specs = [
            {
                "task_type": "research",
                "priority": priority_base,
                "payload": {
                    "topic": goal,
                    "goal_id": goal_id,
                    "stage": "research",
                },
                "key": f"{goal_id}:research",
            },
            {
                "task_type": "planning",
                "priority": priority_base + 10,
                "payload": {
                    "goal": goal,
                    "goal_id": goal_id,
                    "stage": "planning",
                    "depends_on_stage": "research",
                },
                "key": f"{goal_id}:planning",
            },
            {
                "task_type": "build",
                "priority": priority_base + 20,
                "payload": {
                    "name": goal,
                    "goal_id": goal_id,
                    "stage": "build",
                    "depends_on_stage": "planning",
                },
                "key": f"{goal_id}:build",
            },
        ]

        task_ids = []
        task_types = []

        for spec in specs:
            task = self.queue.enqueue(
                task_type=spec["task_type"],
                payload=spec["payload"],
                priority=spec["priority"],
                idempotency_key=spec["key"],
                max_attempts=3,
            )
            task_ids.append(task.task_id)
            task_types.append(task.task_type)

        return GoalDecompositionResult(
            goal_id=goal_id,
            goal=goal,
            tasks_created=len(task_ids),
            task_ids=task_ids,
            task_types=task_types,
        )
