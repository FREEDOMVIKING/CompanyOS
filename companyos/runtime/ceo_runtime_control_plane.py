from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class CEORuntimeControlStatus:
    running: bool
    pid: Optional[int]
    pid_alive: bool
    state_file_present: bool
    ready: bool
    reason: str
    cycle_count: int
    active_orchestrations: int
    completed_orchestrations: int
    failed_orchestrations: int
    halted_orchestrations: int
    consecutive_failures: int


class CEORuntimeControlPlane:
    """
    Detached-process control plane for the Phase 101 autonomous CEO runtime.

    Provides:
    - start
    - status
    - stop
    - duplicate start prevention
    - PID/log persistence

    It does not perform external actions or financial transaction operations.
    """

    def __init__(self) -> None:
        self.home = Path.home()
        self.root = self.home / "companyos"
        self.runtime_dir = self.home / ".companyos_runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

        self.pid_file = self.runtime_dir / "autonomous_ceo_runtime_service.pid"
        self.state_file = self.runtime_dir / "autonomous_ceo_runtime_service.json"
        self.log_file = self.runtime_dir / "autonomous_ceo_runtime_service.log"

    def _read_pid(self) -> Optional[int]:
        try:
            return int(self.pid_file.read_text().strip())
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

    def _read_state(self) -> dict:
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def status(self) -> CEORuntimeControlStatus:
        pid = self._read_pid()
        alive = self._pid_alive(pid)
        state = self._read_state()

        return CEORuntimeControlStatus(
            running=alive,
            pid=pid,
            pid_alive=alive,
            state_file_present=self.state_file.exists(),
            ready=bool(state.get("ready", False)),
            reason=str(state.get("reason", "state_unavailable")),
            cycle_count=int(state.get("cycle_count", 0) or 0),
            active_orchestrations=int(state.get("active_orchestrations", 0) or 0),
            completed_orchestrations=int(state.get("completed_orchestrations", 0) or 0),
            failed_orchestrations=int(state.get("failed_orchestrations", 0) or 0),
            halted_orchestrations=int(state.get("halted_orchestrations", 0) or 0),
            consecutive_failures=int(state.get("consecutive_failures", 0) or 0),
        )

    def start(
        self,
        *,
        interval_seconds: float = 10.0,
        max_failures: int = 5,
    ) -> CEORuntimeControlStatus:
        current = self.status()
        if current.running:
            return current

        try:
            self.pid_file.unlink()
        except FileNotFoundError:
            pass

        cmd = [
            "python",
            str(self.root / "phase101_ceo_runtime_run.py"),
            "--interval",
            str(float(interval_seconds)),
            "--max-failures",
            str(int(max_failures)),
        ]

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{self.root}:{self.root / 'companyos'}"

        with self.log_file.open("ab", buffering=0) as log:
            proc = subprocess.Popen(
                cmd,
                cwd=str(self.root),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

        self.pid_file.write_text(str(proc.pid) + "\n", encoding="utf-8")

        deadline = time.time() + 8.0
        while time.time() < deadline:
            status = self.status()
            if not status.pid_alive:
                break
            if status.state_file_present:
                return status
            time.sleep(0.5)

        return self.status()

    def stop(self, *, timeout_seconds: float = 8.0) -> CEORuntimeControlStatus:
        pid = self._read_pid()
        if not self._pid_alive(pid):
            try:
                self.pid_file.unlink()
            except FileNotFoundError:
                pass
            return self.status()

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

        deadline = time.time() + max(1.0, float(timeout_seconds))
        while time.time() < deadline and self._pid_alive(pid):
            time.sleep(0.25)

        if self._pid_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
            time.sleep(0.25)

        try:
            self.pid_file.unlink()
        except FileNotFoundError:
            pass

        return self.status()
