from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class RuntimeControlStatus:
    running: bool
    pid: Optional[int]
    pid_alive: bool
    state_file_present: bool
    ready: bool
    reason: str
    cycle_count: int
    rpc_ok: bool
    stale: bool
    sol_balance: Optional[float]
    spendable_sol: Optional[float]
    unresolved_records: int
    consecutive_failures: int


class RuntimeControlPlane:
    """
    Start/stop/status control plane for the Phase 89 runtime supervisor.

    Responsibilities:
    - launch supervisor as a detached Termux process
    - persist PID
    - report current supervisor health from persisted state
    - stop only the recorded supervisor PID
    - avoid duplicate supervisor instances

    This control plane does not build, sign, authorize, or broadcast transactions.
    """

    def __init__(self) -> None:
        self.home = Path.home()
        self.root = self.home / "companyos"
        self.runtime_dir = self.home / ".companyos_runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

        self.pid_file = self.runtime_dir / "production_runtime_supervisor.pid"
        self.state_file = self.runtime_dir / "production_runtime_supervisor.json"
        self.log_file = self.runtime_dir / "production_runtime_supervisor.log"

    def _read_pid(self) -> Optional[int]:
        try:
            value = self.pid_file.read_text().strip()
            return int(value)
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

    def status(self) -> RuntimeControlStatus:
        pid = self._read_pid()
        alive = self._pid_alive(pid)
        state = self._read_state()

        return RuntimeControlStatus(
            running=bool(alive),
            pid=pid,
            pid_alive=bool(alive),
            state_file_present=self.state_file.exists(),
            ready=bool(state.get("ready", False)),
            reason=str(state.get("reason", "state_unavailable")),
            cycle_count=int(state.get("cycle_count", 0) or 0),
            rpc_ok=bool(state.get("rpc_ok", False)),
            stale=bool(state.get("stale", True)),
            sol_balance=state.get("sol_balance"),
            spendable_sol=state.get("spendable_sol"),
            unresolved_records=int(state.get("unresolved_records", 0) or 0),
            consecutive_failures=int(state.get("consecutive_failures", 0) or 0),
        )

    def start(
        self,
        *,
        interval_seconds: float = 15.0,
        max_failures: int = 5,
    ) -> RuntimeControlStatus:
        current = self.status()
        if current.running:
            return current

        # Remove stale PID before starting a fresh supervisor.
        try:
            self.pid_file.unlink()
        except FileNotFoundError:
            pass

        cmd = [
            "python",
            str(self.root / "phase89_supervisor_run.py"),
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

        # Give startup a moment to write its first state.
        deadline = time.time() + 8.0
        while time.time() < deadline:
            status = self.status()
            if not status.pid_alive:
                break
            if status.state_file_present and status.ready:
                return status
            time.sleep(0.5)

        return self.status()

    def stop(self, *, timeout_seconds: float = 8.0) -> RuntimeControlStatus:
        pid = self._read_pid()
        if not self._pid_alive(pid):
            try:
                self.pid_file.unlink()
            except FileNotFoundError:
                pass
            return self.status()

        os.kill(pid, signal.SIGTERM)

        deadline = time.time() + max(1.0, float(timeout_seconds))
        while time.time() < deadline:
            if not self._pid_alive(pid):
                break
            time.sleep(0.25)

        if self._pid_alive(pid):
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.25)

        try:
            self.pid_file.unlink()
        except FileNotFoundError:
            pass

        return self.status()
