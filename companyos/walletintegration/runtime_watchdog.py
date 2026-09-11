from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from companyos.walletintegration.runtime_control_plane import RuntimeControlPlane


@dataclass(frozen=True)
class WatchdogDecision:
    action: str
    reason: str
    running: bool
    ready: bool
    rpc_ok: bool
    stale: bool
    unresolved_records: int
    consecutive_failures: int
    restarted: bool
    restart_count: int


class RuntimeWatchdog:
    """
    Supervises the Phase 90 detached runtime process.

    Responsibilities:
    - detect dead supervisor process
    - detect unhealthy persisted runtime state
    - restart the runtime when safe to do so
    - never restart when unresolved SUBMITTED records exist
    - apply restart backoff / restart-count protection
    - persist watchdog state

    The watchdog never builds, signs, authorizes, or broadcasts transactions.
    """

    def __init__(
        self,
        *,
        restart_backoff_seconds: float = 10.0,
        max_restarts_per_window: int = 5,
        restart_window_seconds: float = 600.0,
    ) -> None:
        self.ctl = RuntimeControlPlane()
        self.runtime_dir = Path.home() / ".companyos_runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.runtime_dir / "runtime_watchdog.json"
        self.restart_backoff_seconds = max(1.0, float(restart_backoff_seconds))
        self.max_restarts_per_window = max(1, int(max_restarts_per_window))
        self.restart_window_seconds = max(60.0, float(restart_window_seconds))

    def _load_state(self) -> dict:
        if not self.state_file.exists():
            return {
                "restart_timestamps": [],
                "last_action": "none",
                "last_reason": "new_watchdog",
            }
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {
                "restart_timestamps": [],
                "last_action": "state_reset",
                "last_reason": "watchdog_state_invalid",
            }

    def _save_state(self, data: dict) -> None:
        tmp = self.state_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.state_file)

    def _recent_restarts(self, state: dict) -> list[float]:
        now = time.time()
        values = []
        for value in state.get("restart_timestamps", []):
            try:
                ts = float(value)
            except Exception:
                continue
            if now - ts <= self.restart_window_seconds:
                values.append(ts)
        return values

    def evaluate_once(
        self,
        *,
        interval_seconds: float = 15.0,
        max_failures: int = 5,
    ) -> WatchdogDecision:
        status = self.ctl.status()
        state = self._load_state()
        restarts = self._recent_restarts(state)

        # Never restart into ambiguity.
        if status.unresolved_records > 0:
            state["last_action"] = "blocked"
            state["last_reason"] = "unresolved_submitted_records"
            state["restart_timestamps"] = restarts
            self._save_state(state)
            return WatchdogDecision(
                action="blocked",
                reason="unresolved_submitted_records",
                running=status.running,
                ready=status.ready,
                rpc_ok=status.rpc_ok,
                stale=status.stale,
                unresolved_records=status.unresolved_records,
                consecutive_failures=status.consecutive_failures,
                restarted=False,
                restart_count=len(restarts),
            )

        healthy = bool(
            status.running
            and status.ready
            and status.rpc_ok
            and not status.stale
            and status.consecutive_failures == 0
        )

        if healthy:
            state["last_action"] = "noop"
            state["last_reason"] = "runtime_healthy"
            state["restart_timestamps"] = restarts
            self._save_state(state)
            return WatchdogDecision(
                action="noop",
                reason="runtime_healthy",
                running=True,
                ready=True,
                rpc_ok=True,
                stale=False,
                unresolved_records=0,
                consecutive_failures=0,
                restarted=False,
                restart_count=len(restarts),
            )

        if len(restarts) >= self.max_restarts_per_window:
            state["last_action"] = "blocked"
            state["last_reason"] = "restart_rate_limit_reached"
            state["restart_timestamps"] = restarts
            self._save_state(state)
            return WatchdogDecision(
                action="blocked",
                reason="restart_rate_limit_reached",
                running=status.running,
                ready=status.ready,
                rpc_ok=status.rpc_ok,
                stale=status.stale,
                unresolved_records=status.unresolved_records,
                consecutive_failures=status.consecutive_failures,
                restarted=False,
                restart_count=len(restarts),
            )

        # Clean up a stale/dead process record if needed, then restart.
        if status.running:
            self.ctl.stop()

        time.sleep(self.restart_backoff_seconds)

        started = self.ctl.start(
            interval_seconds=interval_seconds,
            max_failures=max_failures,
        )

        restarted = bool(started.running)
        if restarted:
            restarts.append(time.time())

        state["restart_timestamps"] = restarts
        state["last_action"] = "restart" if restarted else "restart_failed"
        state["last_reason"] = (
            "runtime_restarted"
            if restarted
            else "runtime_restart_failed"
        )
        self._save_state(state)

        return WatchdogDecision(
            action="restart" if restarted else "restart_failed",
            reason="runtime_restarted" if restarted else "runtime_restart_failed",
            running=started.running,
            ready=started.ready,
            rpc_ok=started.rpc_ok,
            stale=started.stale,
            unresolved_records=started.unresolved_records,
            consecutive_failures=started.consecutive_failures,
            restarted=restarted,
            restart_count=len(restarts),
        )
