from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator
from companyos.runtime.ceo_orchestration_journal import CEOOrchestrationJournal


@dataclass
class CEORuntimeServiceState:
    running: bool
    ready: bool
    reason: str
    started_at_unix: float
    last_cycle_unix: float
    cycle_count: int
    active_orchestrations: int
    completed_orchestrations: int
    failed_orchestrations: int
    halted_orchestrations: int
    cycles_dispatched_this_tick: int
    last_orchestration_id: Optional[str]
    consecutive_failures: int
    external_actions_performed: bool
    transaction_broadcasts: bool


class AutonomousCEORuntimeService:
    """
    Continuously advances all persisted non-terminal Phase 100 orchestrations.

    Responsibilities:
    - discover persisted CEO orchestrations
    - advance each RUNNING orchestration by at most one Phase 100 cycle per tick
    - persist service health state atomically
    - journal runtime decisions
    - tolerate one orchestration failure without corrupting others
    - stop after configurable consecutive service failures

    This service performs INTERNAL orchestration only.
    It does NOT send messages, publish, purchase, deploy, sign, or broadcast.
    """

    def __init__(
        self,
        *,
        interval_seconds: float = 10.0,
        max_consecutive_failures: int = 5,
        state_path: Path | None = None,
    ) -> None:
        self.interval_seconds = max(2.0, float(interval_seconds))
        self.max_consecutive_failures = max(1, int(max_consecutive_failures))
        self.ceo = AutonomousCEOOrchestrator()
        self.journal = CEOOrchestrationJournal()
        self.state_path = state_path or (
            Path.home() / ".companyos_runtime" / "autonomous_ceo_runtime_service.json"
        )
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    def _persist(self, state: CEORuntimeServiceState) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(asdict(state), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.state_path)

    def _all_records(self):
        records = []
        for p in sorted(self.ceo.root.glob("*.json")):
            try:
                records.append(self.ceo.load(p.stem))
            except Exception:
                continue
        return records

    def _counts(self):
        active = completed = failed = halted = 0
        for record in self._all_records():
            if record.state == "RUNNING":
                active += 1
            elif record.state == "COMPLETED":
                completed += 1
            elif record.state == "FAILED":
                failed += 1
            elif record.state == "HALTED":
                halted += 1
        return active, completed, failed, halted

    def startup(self) -> CEORuntimeServiceState:
        now = time.time()
        active, completed, failed, halted = self._counts()

        state = CEORuntimeServiceState(
            running=True,
            ready=True,
            reason="ceo_runtime_started",
            started_at_unix=now,
            last_cycle_unix=now,
            cycle_count=0,
            active_orchestrations=active,
            completed_orchestrations=completed,
            failed_orchestrations=failed,
            halted_orchestrations=halted,
            cycles_dispatched_this_tick=0,
            last_orchestration_id=None,
            consecutive_failures=0,
            external_actions_performed=False,
            transaction_broadcasts=False,
        )
        self._persist(state)
        return state

    def cycle(self, state: CEORuntimeServiceState) -> CEORuntimeServiceState:
        now = time.time()
        dispatched = 0
        last_id = None
        service_errors = 0

        for record in self._all_records():
            if record.state != "RUNNING":
                continue

            try:
                result = self.ceo.cycle(record.orchestration_id)
                dispatched += 1
                last_id = record.orchestration_id

                self.journal.append(
                    orchestration_id=result.orchestration_id,
                    event="ceo_runtime_service_cycle",
                    payload=asdict(result),
                )
            except Exception as exc:
                service_errors += 1
                last_id = record.orchestration_id
                self.journal.append(
                    orchestration_id=record.orchestration_id,
                    event="ceo_runtime_service_error",
                    payload={
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:1000],
                    },
                )

        active, completed, failed, halted = self._counts()

        state.running = True
        state.ready = service_errors == 0
        state.reason = "healthy" if service_errors == 0 else "partial_cycle_errors"
        state.last_cycle_unix = now
        state.cycle_count += 1
        state.active_orchestrations = active
        state.completed_orchestrations = completed
        state.failed_orchestrations = failed
        state.halted_orchestrations = halted
        state.cycles_dispatched_this_tick = dispatched
        state.last_orchestration_id = last_id
        state.consecutive_failures = (
            0 if service_errors == 0 else state.consecutive_failures + 1
        )
        state.external_actions_performed = False
        state.transaction_broadcasts = False

        self._persist(state)
        return state

    def run_forever(self) -> None:
        state = self.startup()

        print("COMPANYOS_AUTONOMOUS_CEO_RUNTIME_SERVICE: STARTED")
        print("INTERVAL_SECONDS:", self.interval_seconds)
        print("EXTERNAL_ACTIONS_PERFORMED: False")
        print("TRANSACTION_BROADCASTS: False")

        while not self._stop_requested:
            state = self.cycle(state)

            print(
                f"CYCLE={state.cycle_count} "
                f"READY={state.ready} "
                f"ACTIVE={state.active_orchestrations} "
                f"COMPLETED={state.completed_orchestrations} "
                f"FAILED={state.failed_orchestrations} "
                f"HALTED={state.halted_orchestrations} "
                f"ADVANCED={state.cycles_dispatched_this_tick} "
                f"FAILURES={state.consecutive_failures}"
            )

            if state.consecutive_failures >= self.max_consecutive_failures:
                state.running = False
                state.ready = False
                state.reason = "max_consecutive_failures_reached"
                self._persist(state)
                raise RuntimeError(state.reason)

            time.sleep(self.interval_seconds)
