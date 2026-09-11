from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.ceo_goal_decomposer import CEOGoalDecomposer
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop
from companyos.runtime.goal_lifecycle_manager import GoalLifecycleManager
from companyos.runtime.goal_outcome_evaluator import GoalOutcomeEvaluator


@dataclass
class CEOOrchestrationRecord:
    orchestration_id: str
    root_goal_id: str
    root_goal: str
    state: str
    created_at_unix: float
    updated_at_unix: float
    active_goal_id: Optional[str]
    completed_goal_ids: list[str]
    failed_goal_ids: list[str]
    follow_up_goal_ids: list[str]
    total_cycles: int
    max_cycles: int
    max_follow_up_depth: int
    current_follow_up_depth: int
    last_decision: Optional[str]
    final_summary: Any


@dataclass(frozen=True)
class CEOOrchestrationCycleResult:
    orchestration_id: str
    state: str
    active_goal_id: Optional[str]
    goal_state: Optional[str]
    task_dispatched: bool
    dispatched_agent: Optional[str]
    decision: str
    follow_up_created: bool
    follow_up_goal_id: Optional[str]
    total_cycles: int


class AutonomousCEOOrchestrator:
    """
    Phase 100 milestone orchestration layer.

    Integrates Phases 94-99 into one bounded, restart-safe internal CEO loop:

      CEO goal
        -> decompose
        -> dependency-aware specialist execution
        -> lifecycle refresh
        -> outcome evaluation
        -> optional bounded follow-up goal
        -> terminal orchestration result

    IMPORTANT:
    - Internal orchestration only.
    - Does NOT sign or broadcast transactions.
    - Does NOT send emails/messages, publish, purchase, deploy, or perform
      irreversible external actions.
    - Follow-up generation is bounded by max_follow_up_depth and max_cycles.
    """

    def __init__(
        self,
        *,
        queue: AutonomousTaskQueue | None = None,
        root: Path | None = None,
    ) -> None:
        self.queue = queue or AutonomousTaskQueue()
        self.decomposer = CEOGoalDecomposer(self.queue)
        self.execution_loop = AutonomousGoalExecutionLoop(self.queue)

        runtime_root = root or (Path.home() / ".companyos_runtime")
        self.root = runtime_root / "ceo_orchestrations"
        self.goal_root = runtime_root / "goal_lifecycle"
        self.outcome_root = runtime_root / "goal_outcomes"
        self.root.mkdir(parents=True, exist_ok=True)

        self.lifecycle = GoalLifecycleManager(self.queue, self.goal_root)
        self.evaluator = GoalOutcomeEvaluator(self.lifecycle, self.outcome_root)

    def _path(self, orchestration_id: str) -> Path:
        return self.root / f"{orchestration_id}.json"

    def save(self, record: CEOOrchestrationRecord) -> None:
        path = self._path(record.orchestration_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(asdict(record), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)

    def load(self, orchestration_id: str) -> CEOOrchestrationRecord:
        data = json.loads(self._path(orchestration_id).read_text(encoding="utf-8"))
        return CEOOrchestrationRecord(**data)

    def start(
        self,
        *,
        goal: str,
        orchestration_id: str | None = None,
        max_cycles: int = 100,
        max_follow_up_depth: int = 2,
        priority_base: int = 100,
    ) -> CEOOrchestrationRecord:
        goal = goal.strip()
        if not goal:
            raise ValueError("goal_empty")

        orchestration_id = orchestration_id or str(uuid.uuid4())
        root_goal_id = f"{orchestration_id}:goal:0"

        # Idempotent decomposition keys in Phase 96 make this safe to call again.
        self.decomposer.decompose(
            goal=goal,
            priority_base=priority_base,
            goal_id=root_goal_id,
        )

        now = time.time()
        record = CEOOrchestrationRecord(
            orchestration_id=orchestration_id,
            root_goal_id=root_goal_id,
            root_goal=goal,
            state="RUNNING",
            created_at_unix=now,
            updated_at_unix=now,
            active_goal_id=root_goal_id,
            completed_goal_ids=[],
            failed_goal_ids=[],
            follow_up_goal_ids=[],
            total_cycles=0,
            max_cycles=max(1, int(max_cycles)),
            max_follow_up_depth=max(0, int(max_follow_up_depth)),
            current_follow_up_depth=0,
            last_decision="root_goal_created",
            final_summary=None,
        )
        self.save(record)
        return record

    def _goal_text(self, goal_id: str, record: CEOOrchestrationRecord) -> str:
        if goal_id == record.root_goal_id:
            return record.root_goal

        try:
            outcome_path = self.outcome_root / f"{goal_id}.json"
            if outcome_path.exists():
                data = json.loads(outcome_path.read_text(encoding="utf-8"))
                follow = data.get("follow_up_goal")
                if follow:
                    return str(follow)
        except Exception:
            pass

        # Recover goal wording from queued task payloads.
        for task in self.queue.all_tasks():
            payload = task.payload or {}
            if payload.get("goal_id") == goal_id:
                return str(
                    payload.get("goal")
                    or payload.get("topic")
                    or payload.get("name")
                    or goal_id
                )
        return goal_id

    def _create_follow_up(
        self,
        record: CEOOrchestrationRecord,
        *,
        goal_text: str,
    ) -> str:
        next_depth = record.current_follow_up_depth + 1
        goal_id = f"{record.orchestration_id}:goal:{next_depth}"

        self.decomposer.decompose(
            goal=goal_text,
            priority_base=100 + (next_depth * 20),
            goal_id=goal_id,
        )

        if goal_id not in record.follow_up_goal_ids:
            record.follow_up_goal_ids.append(goal_id)

        record.current_follow_up_depth = next_depth
        record.active_goal_id = goal_id
        record.last_decision = "follow_up_goal_created"
        record.updated_at_unix = time.time()
        self.save(record)
        return goal_id

    def cycle(self, orchestration_id: str) -> CEOOrchestrationCycleResult:
        record = self.load(orchestration_id)

        if record.state in ("COMPLETED", "FAILED", "HALTED"):
            return CEOOrchestrationCycleResult(
                orchestration_id=record.orchestration_id,
                state=record.state,
                active_goal_id=record.active_goal_id,
                goal_state=None,
                task_dispatched=False,
                dispatched_agent=None,
                decision="terminal_noop",
                follow_up_created=False,
                follow_up_goal_id=None,
                total_cycles=record.total_cycles,
            )

        if record.total_cycles >= record.max_cycles:
            record.state = "HALTED"
            record.last_decision = "max_cycles_reached"
            record.final_summary = {
                "reason": "max_cycles_reached",
                "completed_goal_ids": record.completed_goal_ids,
                "failed_goal_ids": record.failed_goal_ids,
                "follow_up_goal_ids": record.follow_up_goal_ids,
            }
            record.updated_at_unix = time.time()
            self.save(record)
            return CEOOrchestrationCycleResult(
                record.orchestration_id,
                record.state,
                record.active_goal_id,
                None,
                False,
                None,
                "max_cycles_reached",
                False,
                None,
                record.total_cycles,
            )

        active_goal_id = record.active_goal_id
        if not active_goal_id:
            record.state = "FAILED"
            record.last_decision = "active_goal_missing"
            record.updated_at_unix = time.time()
            self.save(record)
            return CEOOrchestrationCycleResult(
                record.orchestration_id,
                record.state,
                None,
                None,
                False,
                None,
                "active_goal_missing",
                False,
                None,
                record.total_cycles,
            )

        goal_text = self._goal_text(active_goal_id, record)

        # First advance at most one dependency-ready task.
        dispatch = self.execution_loop.cycle()

        # Then derive whole-goal lifecycle.
        goal_record = self.lifecycle.refresh(
            goal_id=active_goal_id,
            goal=goal_text,
        )

        record.total_cycles += 1
        record.updated_at_unix = time.time()

        follow_up_created = False
        follow_up_goal_id = None
        decision = "continue_execution"

        if goal_record.state in ("COMPLETED", "FAILED", "BLOCKED"):
            evaluation = self.evaluator.evaluate(
                goal_id=active_goal_id,
                goal=goal_text,
            )

            if evaluation.goal_state == "COMPLETED":
                if active_goal_id not in record.completed_goal_ids:
                    record.completed_goal_ids.append(active_goal_id)

                # Phase 99 completed goals recommend review/decision, but
                # Phase 100 intentionally treats successful internal completion
                # as terminal unless a later phase adds a policy-approved
                # expansion engine.
                record.state = "COMPLETED"
                record.last_decision = "root_or_followup_goal_completed"
                record.final_summary = {
                    "success": True,
                    "root_goal": record.root_goal,
                    "active_goal_id": active_goal_id,
                    "completed_goal_ids": record.completed_goal_ids,
                    "follow_up_goal_ids": record.follow_up_goal_ids,
                    "evaluation": asdict(evaluation),
                }
                decision = "orchestration_completed"

            elif evaluation.goal_state in ("FAILED", "BLOCKED"):
                if active_goal_id not in record.failed_goal_ids:
                    record.failed_goal_ids.append(active_goal_id)

                can_follow = (
                    bool(evaluation.follow_up_goal)
                    and record.current_follow_up_depth < record.max_follow_up_depth
                )

                if can_follow:
                    follow_up_goal_id = self._create_follow_up(
                        record,
                        goal_text=evaluation.follow_up_goal or "",
                    )
                    follow_up_created = True
                    decision = "follow_up_goal_created"
                else:
                    record.state = "FAILED"
                    record.last_decision = "goal_failed_no_follow_up_budget"
                    record.final_summary = {
                        "success": False,
                        "root_goal": record.root_goal,
                        "failed_goal_ids": record.failed_goal_ids,
                        "follow_up_goal_ids": record.follow_up_goal_ids,
                        "evaluation": asdict(evaluation),
                    }
                    decision = "orchestration_failed"

        self.save(record)

        return CEOOrchestrationCycleResult(
            orchestration_id=record.orchestration_id,
            state=record.state,
            active_goal_id=record.active_goal_id,
            goal_state=goal_record.state,
            task_dispatched=dispatch.dispatched,
            dispatched_agent=dispatch.agent_name,
            decision=decision,
            follow_up_created=follow_up_created,
            follow_up_goal_id=follow_up_goal_id,
            total_cycles=record.total_cycles,
        )

    def run_until_terminal(
        self,
        orchestration_id: str,
        *,
        max_runner_cycles: int = 200,
        sleep_seconds: float = 0.0,
    ) -> list[CEOOrchestrationCycleResult]:
        results = []

        for _ in range(max(1, int(max_runner_cycles))):
            result = self.cycle(orchestration_id)
            results.append(result)

            if result.state in ("COMPLETED", "FAILED", "HALTED"):
                break

            if sleep_seconds > 0:
                time.sleep(float(sleep_seconds))

        return results
