from __future__ import annotations
import json, os, signal, subprocess, sys, time
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class LaunchStatus:
    unified_runtime_running: bool
    continuous_goal_runtime_running: bool
    launch_ready: bool
    reason: str
    unified_pid: int | None
    goal_runtime_pid: int | None

class LaunchRuntime:
    def __init__(self):
        self.home = Path.home()
        self.root = self.home / "companyos"
        self.runtime = self.home / ".companyos_runtime"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.unified_pid = self.runtime / "phase109_116_unified.pid"
        self.goal_pid = self.runtime / "continuous_goal_runtime.pid"

    @staticmethod
    def alive(pid):
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except Exception:
            return False

    @staticmethod
    def read_pid(path):
        try:
            return int(path.read_text().strip())
        except Exception:
            return None

    def status(self):
        upid = self.read_pid(self.unified_pid)
        gpid = self.read_pid(self.goal_pid)
        ur = self.alive(upid)
        gr = self.alive(gpid)
        ready = ur and gr
        reason = "launch_stack_healthy" if ready else (
            "unified_runtime_not_running" if not ur else "goal_runtime_not_running"
        )
        return LaunchStatus(ur, gr, ready, reason, upid, gpid)

    def start(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{self.root}:{self.root/'companyos'}"

        # Start Phase 102 unified runtime in a detached process.
        if not self.alive(self.read_pid(self.unified_pid)):
            log = (self.runtime / "launch_unified_runtime.log").open("ab")
            p = subprocess.Popen(
                [sys.executable, str(self.root/"phase102_unified_runtime_ctl.py"), "start",
                 "--financial-supervisor-interval","15",
                 "--watchdog-check-every","30",
                 "--financial-max-failures","5",
                 "--restart-backoff","5",
                 "--ceo-interval","10",
                 "--ceo-max-failures","5"],
                cwd=str(self.root), env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True
            )
            self.unified_pid.write_text(str(p.pid))

        # Start Phase 104 continuous goal runtime.
        subprocess.run(
            [sys.executable, str(self.root/"phase104_runtime_ctl.py"), "start",
             "--interval","10","--max-failures","5"],
            cwd=str(self.root), env=env, check=False
        )
        time.sleep(2)
        return self.status()

    def stop(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{self.root}:{self.root/'companyos'}"
        subprocess.run([sys.executable, str(self.root/"phase104_runtime_ctl.py"), "stop"],
                       cwd=str(self.root), env=env, check=False)
        subprocess.run([sys.executable, str(self.root/"phase102_unified_runtime_ctl.py"), "stop"],
                       cwd=str(self.root), env=env, check=False)
        pid = self.read_pid(self.unified_pid)
        if self.alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
        self.unified_pid.unlink(missing_ok=True)
        time.sleep(1)
        return self.status()
