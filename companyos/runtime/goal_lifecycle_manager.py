from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue


@dataclass
class GoalRecord:
    goal_id: str
    goal: str
    state: str
    created_at_unix: float
    updated_at_unix: float
    completed_at_unix: Optional[float]
    failed_at_unix: Optional[float]
    task_ids: list[str]
    completed_tasks: int
    failed_tasks: int
    queued_tasks: int
    running_tasks: int
    blocked: bool
    final_result: Any
    last_error: Optional[str]


class GoalLifecycleManager:
    """
    Tracks CEO-level goal state across all underlying specialist tasks.

    Goal states:
      ACTIVE
      EXECUTING
      COMPLETED
      FAILED
      BLOCKED

    The manager derives goal state from persisted Phase 94 task records and
    aggregates task outputs into a CEO-level result.
    """

    def __init__(
        self,
        queue: AutonomousTaskQueue | None = None,
        root: Path | None = None,
    ) -> None:
        self.queue = queue or AutonomousTaskQueue()
        self.root = root or (Path.home() / ".companyos_runtime" / "goal_lifecycle")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, goal_id: str) -> Path:
        return self.root / f"{goal_id}.json"

    def save(self, record: GoalRecord) -> None:
        path = self._path(record.goal_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(asdict(record), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    def load(self, goal_id: str) -> GoalRecord:
        data = json.loads(self._path(goal_id).read_text(encoding="utf-8"))
        return GoalRecord(**data)

    def ensure_goal(self, *, goal_id: str, goal: str) -> GoalRecord:
        path = self._path(goal_id)
        if path.exists():
            return self.load(goal_id)

        now = time.time()
        record = GoalRecord(
            goal_id=goal_id,
            goal=goal,
            state="ACTIVE",
            created_at_unix=now,
            updated_at_unix=now,
            completed_at_unix=None,
            failed_at_unix=None,
            task_ids=[],
            completed_tasks=0,
            failed_tasks=0,
            queued_tasks=0,
            running_tasks=0,
            blocked=False,
            final_result=None,
            last_error=None,
        )
        self.save(record)
        return record

    def refresh(self, *, goal_id: str, goal: str = "") -> GoalRecord:
        record = self.ensure_goal(goal_id=goal_id, goal=goal or goal_id)

        all_tasks = []
        for task in self.queue.all_tasks():
            payload = task.payload or {}
            if payload.get("goal_id") == goal_id:
                all_tasks.append(task)

        # V65.82 semantic duplicate cancellation lifecycle filter
        # A reconciliation tombstone is audit history, not unfinished goal work.
        # General CANCELLED tasks are NOT ignored.
        tasks = []
        for task in all_tasks:
            ignored_duplicate = (
                task.state == "CANCELLED"
                and isinstance(task.result, dict)
                and task.result.get("reason") == "semantic_duplicate_already_completed"
                and bool(task.result.get("canonical_task_id"))
            )
            if not ignored_duplicate:
                tasks.append(task)

        record.task_ids = [t.task_id for t in tasks]
        record.completed_tasks = sum(1 for t in tasks if t.state == "COMPLETED")
        record.failed_tasks = sum(1 for t in tasks if t.state == "FAILED")
        record.queued_tasks = sum(1 for t in tasks if t.state == "QUEUED")
        record.running_tasks = sum(1 for t in tasks if t.state in ("CLAIMED", "RUNNING"))

        now = time.time()
        record.updated_at_unix = now
        record.blocked = False
        record.last_error = None

        if not tasks:
            record.state = "ACTIVE"
            record.final_result = None
            self.save(record)
            return record

        if record.failed_tasks > 0:
            record.state = "FAILED"
            record.failed_at_unix = record.failed_at_unix or now
            failed = [t for t in tasks if t.state == "FAILED"]
            record.last_error = "; ".join(
                [t.last_error or f"{t.task_type}_failed" for t in failed]
            )[:2000]
            self.save(record)
            return record

        if record.completed_tasks == len(tasks):
            record.state = "COMPLETED"
            record.completed_at_unix = record.completed_at_unix or now
            ordered = sorted(tasks, key=lambda t: (t.priority, t.created_at_unix))
            record.final_result = {
                "goal_id": goal_id,
                "goal": record.goal,
                "outputs": [
                    {
                        "task_id": t.task_id,
                        "task_type": t.task_type,
                        "agent": t.assigned_agent,
                        "result": t.result,
                    }
                    for t in ordered
                ],
            }
            self.save(record)
            return record

        # Detect dependency block: queued tasks remain, none running, and no
        # queued task has its dependency satisfied.
        if record.queued_tasks > 0 and record.running_tasks == 0:
            by_stage = {}
            for t in tasks:
                stage = (t.payload or {}).get("stage")
                if stage:
                    by_stage[stage] = t

            ready_exists = False
            for t in tasks:
                if t.state != "QUEUED":
                    continue
                dep = (t.payload or {}).get("depends_on_stage")
                if not dep:
                    ready_exists = True
                    break
                dep_task = by_stage.get(dep)
                if dep_task and dep_task.state == "COMPLETED":
                    ready_exists = True
                    break

            if not ready_exists:
                record.state = "BLOCKED"
                record.blocked = True
                record.last_error = "no_dependency_ready_task"
                self.save(record)
                return record

        record.state = "EXECUTING"
        record.final_result = None
        self.save(record)
        return record
