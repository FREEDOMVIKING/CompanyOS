from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from companyos.walletintegration.runtime_control_plane import RuntimeControlPlane


@dataclass(frozen=True)
class RuntimeServiceStatus:
    supervisor_running: bool
    supervisor_pid: Optional[int]
    supervisor_ready: bool
    supervisor_rpc_ok: bool
    supervisor_stale: bool
    unresolved_records: int
    watchdog_running: bool
    watchdog_pid: Optional[int]
    service_ready: bool
    reason: str


class RuntimeServiceManager:
    """
    Coordinates the detached runtime supervisor + detached watchdog.

    Goals:
    - one START command for the production runtime stack
    - one STATUS command for both processes
    - one STOP command for both processes
    - avoid duplicate watchdog instances
    - preserve Phase 90/91 safety behavior

    This manager never builds, signs, authorizes, or broadcasts transactions.
    """

    def __init__(self) -> None:
        self.home = Path.home()
        self.root = self.home / "companyos"
        self.runtime_dir = self.home / ".companyos_runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

        self.supervisor_ctl = RuntimeControlPlane()

        self.watchdog_pid_file = self.runtime_dir / "runtime_watchdog.pid"
        self.watchdog_log_file = self.runtime_dir / "runtime_watchdog.log"

    def _read_pid(self, path: Path) -> Optional[int]:
        try:
            return int(path.read_text().strip())
        except Exception:
            return None

    def _pid_alive(self, pid: Optional[int]) -> bool:
        if not pid or pid <= 1:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _watchdog_status(self) -> tuple[bool, Optional[int]]:
        pid = self._read_pid(self.watchdog_pid_file)
        return self._pid_alive(pid), pid

    def status(self) -> RuntimeServiceStatus:
        sup = self.supervisor_ctl.status()
        watchdog_running, watchdog_pid = self._watchdog_status()

        ready = bool(
            sup.running
            and sup.ready
            and sup.rpc_ok
            and not sup.stale
            and sup.unresolved_records == 0
            and watchdog_running
        )

        if ready:
            reason = "service_stack_healthy"
        elif sup.unresolved_records > 0:
            reason = "unresolved_submitted_records"
        elif not sup.running:
            reason = "supervisor_not_running"
        elif not watchdog_running:
            reason = "watchdog_not_running"
        elif not sup.ready:
            reason = "supervisor_not_ready"
        elif not sup.rpc_ok or sup.stale:
            reason = "supervisor_rpc_unhealthy"
        else:
            reason = "service_stack_not_ready"

        return RuntimeServiceStatus(
            supervisor_running=sup.running,
            supervisor_pid=sup.pid,
            supervisor_ready=sup.ready,
            supervisor_rpc_ok=sup.rpc_ok,
            supervisor_stale=sup.stale,
            unresolved_records=sup.unresolved_records,
            watchdog_running=watchdog_running,
            watchdog_pid=watchdog_pid,
            service_ready=ready,
            reason=reason,
        )

    def start(
        self,
        *,
        supervisor_interval: float = 15.0,
        watchdog_check_every: float = 30.0,
        max_failures: int = 5,
        restart_backoff: float = 5.0,
    ) -> RuntimeServiceStatus:
        sup = self.supervisor_ctl.status()

        if sup.unresolved_records > 0:
            return self.status()

        if not sup.running:
            self.supervisor_ctl.start(
                interval_seconds=supervisor_interval,
                max_failures=max_failures,
            )

        watchdog_running, watchdog_pid = self._watchdog_status()
        if not watchdog_running:
            try:
                self.watchdog_pid_file.unlink()
            except FileNotFoundError:
                pass

            cmd = [
                "python",
                str(self.root / "phase91_watchdog_loop.py"),
                "--check-every",
                str(float(watchdog_check_every)),
                "--runtime-interval",
                str(float(supervisor_interval)),
                "--max-failures",
                str(int(max_failures)),
                "--restart-backoff",
                str(float(restart_backoff)),
            ]

            env = os.environ.copy()
            env["PYTHONPATH"] = f"{self.root}:{self.root / 'companyos'}"

            with self.watchdog_log_file.open("ab", buffering=0) as log:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(self.root),
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )

            self.watchdog_pid_file.write_text(str(proc.pid) + "\n", encoding="utf-8")

        deadline = time.time() + 8.0
        while time.time() < deadline:
            status = self.status()
            if status.service_ready:
                return status
            time.sleep(0.5)

        return self.status()

    def stop(self, *, timeout_seconds: float = 8.0) -> RuntimeServiceStatus:
        watchdog_pid = self._read_pid(self.watchdog_pid_file)
        if self._pid_alive(watchdog_pid):
            try:
                os.kill(watchdog_pid, signal.SIGTERM)
            except OSError:
                pass

            deadline = time.time() + max(1.0, float(timeout_seconds))
            while time.time() < deadline and self._pid_alive(watchdog_pid):
                time.sleep(0.25)

            if self._pid_alive(watchdog_pid):
                try:
                    os.kill(watchdog_pid, signal.SIGKILL)
                except OSError:
                    pass

        try:
            self.watchdog_pid_file.unlink()
        except FileNotFoundError:
            pass

        self.supervisor_ctl.stop(timeout_seconds=timeout_seconds)
        return self.status()
