from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional


VALID_STATES = {
    "QUEUED",
    "CLAIMED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
}


@dataclass
class TaskRecord:
    task_id: str
    idempotency_key: str
    task_type: str
    priority: int
    payload: dict[str, Any]
    state: str
    assigned_agent: Optional[str]
    attempts: int
    max_attempts: int
    created_at_unix: float
    updated_at_unix: float
    next_attempt_unix: float
    result: Any
    last_error: Optional[str]


class AutonomousTaskQueue:
    """
    Persistent internal task queue for CompanyOS.

    Features:
    - durable JSON-backed tasks
    - priority ordering
    - idempotency-key duplicate protection
    - claim/run/complete/fail lifecycle
    - retry scheduling
    - stale CLAIMED/RUNNING recovery after restart

    This queue does NOT sign, broadcast, or move funds.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".companyos_runtime" / "task_queue")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        return self.root / f"{task_id}.json"

    def save(self, task: TaskRecord) -> None:
        path = self._path(task.task_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(task), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(path)

    def load(self, task_id: str) -> TaskRecord:
        data = json.loads(self._path(task_id).read_text(encoding="utf-8"))
        return TaskRecord(**data)

    def _iter_task_files(self):
        for path in self.root.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                yield TaskRecord(**data)
            except Exception:
                continue

    def all_tasks(self) -> list[TaskRecord]:
        return list(self._iter_task_files())

    def bounded_candidates_window(self, limit: int = 1000, offset: int = 0) -> list[TaskRecord]:
        limit=max(1,int(limit)); offset=max(0,int(offset))
        files=self._iter_task_files() if hasattr(self,"_iter_task_files") else list(self.root.glob("*.json"))
        if not files: return []
        start=offset % len(files); ordered=files[start:]+files[:start]; tasks=[]
        for path in ordered[:limit]:
            try:
                data=json.loads(path.read_text(encoding="utf-8")); tasks.append(TaskRecord(**data))
            except Exception: continue
        return tasks

    def bounded_candidates(self, limit: int = 512) -> list[TaskRecord]:
        limit = max(1, int(limit))
        candidates = []
        for task in self._iter_task_files():
            if task.state != "QUEUED":
                continue
            if task.attempts >= task.max_attempts:
                continue
            candidates.append(task)
        candidates.sort(key=lambda t: (-int(t.priority), float(t.created_at_unix)))
        return candidates[:limit]

    def has_completed_goal_stage(self, goal_id: str, stage: str) -> bool:
        for task in self._iter_task_files():
            payload = task.payload if isinstance(task.payload, dict) else {}
            if payload.get("goal_id") == goal_id and payload.get("stage") == stage and task.state == "COMPLETED":
                return True
        return False

    def find_by_idempotency_key(self, key: str) -> Optional[TaskRecord]:
        if not key:
            return None
        for task in self.all_tasks():
            if task.idempotency_key == key:
                return task
        return None

    def enqueue(
        self,
        *,
        task_type: str,
        payload: dict[str, Any],
        priority: int = 100,
        idempotency_key: str = "",
        max_attempts: int = 3,
    ) -> TaskRecord:
        existing = self.find_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        now = time.time()
        task = TaskRecord(
            task_id=str(uuid.uuid4()),
            idempotency_key=idempotency_key,
            task_type=task_type,
            priority=int(priority),
            payload=dict(payload),
            state="QUEUED",
            assigned_agent=None,
            attempts=0,
            max_attempts=max(1, int(max_attempts)),
            created_at_unix=now,
            updated_at_unix=now,
            next_attempt_unix=now,
            result=None,
            last_error=None,
        )
        self.save(task)
        return task

    def claim_next(self, *, agent_name: str) -> Optional[TaskRecord]:
        now = time.time()
        candidates = [
            t for t in self.all_tasks()
            if t.state == "QUEUED"
            and t.next_attempt_unix <= now
            and t.attempts < t.max_attempts
        ]
        if not candidates:
            return None

        candidates.sort(key=lambda t: (t.priority, t.created_at_unix))
        task = candidates[0]
        task.state = "CLAIMED"
        task.assigned_agent = agent_name
        task.updated_at_unix = now
        self.save(task)
        return task

    def mark_running(self, task: TaskRecord) -> TaskRecord:
        task.state = "RUNNING"
        task.attempts += 1
        task.updated_at_unix = time.time()
        self.save(task)
        return task

    def complete(self, task: TaskRecord, result: Any) -> TaskRecord:
        task.state = "COMPLETED"
        task.result = result
        task.last_error = None
        task.updated_at_unix = time.time()
        self.save(task)
        return task

    def fail(
        self,
        task: TaskRecord,
        error: str,
        *,
        retry_delay_seconds: float = 30.0,
    ) -> TaskRecord:
        task.last_error = str(error)[:1000]
        task.updated_at_unix = time.time()

        if task.attempts < task.max_attempts:
            task.state = "QUEUED"
            task.assigned_agent = None
            task.next_attempt_unix = time.time() + max(0.0, float(retry_delay_seconds))
        else:
            task.state = "FAILED"

        self.save(task)
        return task

    def recover_stale(
        self,
        *,
        stale_after_seconds: float = 300.0,
    ) -> list[TaskRecord]:
        now = time.time()
        recovered = []

        for task in self.all_tasks():
            if task.state not in ("CLAIMED", "RUNNING"):
                continue

            age = now - task.updated_at_unix
            if age < stale_after_seconds:
                continue

            task.assigned_agent = None

            if task.attempts < task.max_attempts:
                task.state = "QUEUED"
                task.next_attempt_unix = now
                task.last_error = "recovered_after_restart_or_stale_worker"
            else:
                task.state = "FAILED"
                task.last_error = "max_attempts_exhausted_during_recovery"

            task.updated_at_unix = now
            self.save(task)
            recovered.append(task)

        return recovered
