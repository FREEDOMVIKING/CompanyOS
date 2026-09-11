from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Any


@dataclass
class GoalIntakeRecord:
    intake_id: str
    goal: str
    priority: int
    state: str
    created_at_unix: float
    updated_at_unix: float
    orchestration_id: Optional[str]
    attempts: int
    max_attempts: int
    last_error: Optional[str]
    metadata: dict[str, Any]


class AutonomousGoalIntake:
    """
    Durable inbox for new CEO-level goals.

    States:
      PENDING
      CLAIMED
      SUBMITTED
      FAILED
      CANCELLED

    This inbox itself performs no external actions and no transaction operations.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".companyos_runtime" / "goal_intake")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, intake_id: str) -> Path:
        return self.root / f"{intake_id}.json"

    def save(self, record: GoalIntakeRecord) -> None:
        path = self._path(record.intake_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(asdict(record), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    def load(self, intake_id: str) -> GoalIntakeRecord:
        data = json.loads(self._path(intake_id).read_text(encoding="utf-8"))
        return GoalIntakeRecord(**data)

    def all_records(self) -> list[GoalIntakeRecord]:
        records = []
        for p in self.root.glob("*.json"):
            try:
                records.append(self.load(p.stem))
            except Exception:
                continue
        return records

    def submit(
        self,
        *,
        goal: str,
        priority: int = 100,
        metadata: dict[str, Any] | None = None,
        intake_id: str | None = None,
        max_attempts: int = 3,
    ) -> GoalIntakeRecord:
        goal = goal.strip()
        if not goal:
            raise ValueError("goal_empty")

        intake_id = intake_id or str(uuid.uuid4())
        path = self._path(intake_id)
        if path.exists():
            return self.load(intake_id)

        now = time.time()
        record = GoalIntakeRecord(
            intake_id=intake_id,
            goal=goal,
            priority=int(priority),
            state="PENDING",
            created_at_unix=now,
            updated_at_unix=now,
            orchestration_id=None,
            attempts=0,
            max_attempts=max(1, int(max_attempts)),
            last_error=None,
            metadata=dict(metadata or {}),
        )
        self.save(record)
        return record

    def claim_next(self) -> Optional[GoalIntakeRecord]:
        pending = [
            r for r in self.all_records()
            if r.state == "PENDING" and r.attempts < r.max_attempts
        ]
        if not pending:
            return None

        pending.sort(key=lambda r: (r.priority, r.created_at_unix))
        record = pending[0]
        record.state = "CLAIMED"
        record.attempts += 1
        record.updated_at_unix = time.time()
        self.save(record)
        return record

    def mark_submitted(
        self,
        record: GoalIntakeRecord,
        *,
        orchestration_id: str,
    ) -> GoalIntakeRecord:
        record.state = "SUBMITTED"
        record.orchestration_id = orchestration_id
        record.last_error = None
        record.updated_at_unix = time.time()
        self.save(record)
        return record

    def fail(self, record: GoalIntakeRecord, error: str) -> GoalIntakeRecord:
        record.last_error = str(error)[:1000]
        record.updated_at_unix = time.time()

        if record.attempts < record.max_attempts:
            record.state = "PENDING"
        else:
            record.state = "FAILED"

        self.save(record)
        return record

    def recover_claimed(self) -> int:
        recovered = 0
        for record in self.all_records():
            if record.state != "CLAIMED":
                continue
            if record.attempts < record.max_attempts:
                record.state = "PENDING"
            else:
                record.state = "FAILED"
            record.last_error = "recovered_after_restart"
            record.updated_at_unix = time.time()
            self.save(record)
            recovered += 1
        return recovered
