from __future__ import annotations

import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ManagedService:
    name: str
    argv: tuple[str, ...]


class ServiceSupervisor:
    @staticmethod
    def _load_launch_env_file(path: Path) -> None:
        import shlex
        if not path.exists():
            return
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                parts = shlex.split(line, posix=True)
            except Exception:
                continue
            if not parts:
                continue
            if parts[0] == "export":
                parts = parts[1:]
            if not parts:
                continue
            token = parts[0]
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value

    def __init__(self, services: Iterable[ManagedService] | None = None):
        self.root = (Path.home() / "companyos").resolve()
        self._load_launch_env_file(Path.home() / ".companyos_launch_env")
        # V30_SHARED_RUNTIME_ROOT
        self.runtime_root = Path.home() / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)

        self.state_path = self.runtime_root / "service_supervisor_state.json"
        # COMPANYOS_SERVICE_SUPERVISOR_STOP_PATH_V28
        self.stop_path = self.runtime_root / "SUPERVISOR_STOP"
        self.log_path = self.runtime_root / "service_supervisor.log"
        self.lock_path = self.runtime_root / "service_supervisor.lock"

        self.poll_seconds = max(
            1.0, float(os.getenv("COMPANYOS_SUPERVISOR_POLL_SECONDS", "5"))
        )
        self.base_backoff = max(
            1.0, float(os.getenv("COMPANYOS_SUPERVISOR_BACKOFF_SECONDS", "2"))
        )
        self.max_backoff = max(
            self.base_backoff,
            float(os.getenv("COMPANYOS_SUPERVISOR_MAX_BACKOFF_SECONDS", "60")),
        )

        self.services = list(services or self.default_services())
        self.children: dict[str, subprocess.Popen] = {}
        self.failures = {s.name: 0 for s in self.services}
        self.restarts = {s.name: 0 for s in self.services}
        self.started_at = time.time()
        # V32_STABILITY_WINDOW
        self.spawned_at: dict[str, float] = {}
        self._stopping = False
        self._lock_file = None

    @staticmethod
    def default_services() -> list[ManagedService]:
        python = sys.executable
        services = [
            ManagedService("continuous_goal_runtime", (python, "-c", "from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime; ContinuousGoalRuntime().run()")),
            ManagedService("productive_autonomy_watchdog", (python, "-m", "companyos.runtime.productive_autonomy_watchdog")),
            ManagedService("local_dashboard", (python, "-m", "companyos.runtime.dashboard_server")),
        ]
        if (Path.home()/"companyos/companyos/runtime/profit_opportunity_runtime.py").exists():
            services.append(ManagedService("profit_opportunity_runtime", (python, "-m", "companyos.runtime.profit_opportunity_runtime")))
        if (
            os.getenv("COMPANYOS_ENABLE_SELF_EVOLUTION", "0") == "1"
            and (Path.home()/"companyos/companyos/runtime/self_evolution_runtime.py").exists()
        ):
            services.append(ManagedService("self_evolution_runtime", (python, "-m", "companyos.runtime.self_evolution_runtime")))
        # COMPANYOS_V69_31_EXTERNAL_RESEARCH_SERVICE
        if (Path.home()/"companyos/companyos/runtime/external_research_network_worker.py").exists():
            services.append(
                ManagedService(
                    "external_research_network",
                    (python, "-m", "companyos.runtime.external_research_network_worker"),
                )
            )
        # COMPANYOS_V69_32_LIVE_MARKET_INTELLIGENCE_SERVICE
        if (Path.home()/"companyos/companyos/runtime/live_market_intelligence.py").exists():
            services.append(
                ManagedService(
                    "live_market_intelligence",
                    (python, "-m", "companyos.runtime.live_market_intelligence", "run"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/autonomous_diagnostics.py").exists():
            services.append(
                ManagedService(
                    "autonomous_diagnostics",
                    (python, "-m", "companyos.runtime.autonomous_diagnostics"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/capability_expansion.py").exists():
            services.append(ManagedService("capability_expansion", (python, "-m", "companyos.runtime.capability_expansion", "run")))
        if (Path.home()/"companyos/companyos/runtime/capability_feedback.py").exists():
            services.append(ManagedService("capability_feedback", (python, "-m", "companyos.runtime.capability_feedback", "run")))
            services.append(ManagedService("compounding_capability_expansion", (python, "-m", "companyos.runtime.compounding_capability_expansion")))
        if (Path.home()/"companyos/companyos/runtime/capability_request_executor.py").exists():
            services.append(
                ManagedService(
                    "capability_request_executor",
                    (python, "-m", "companyos.runtime.capability_request_executor", "run"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/recursive_improvement_controller.py").exists():
            services.append(
                ManagedService(
                    "recursive_improvement_controller",
                    (python, "-m", "companyos.runtime.recursive_improvement_controller", "run"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/semantic_capability_bridge.py").exists():
            services.append(
                ManagedService(
                    "semantic_capability_bridge",
                    (python, "-m", "companyos.runtime.semantic_capability_bridge", "run"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/opportunity_execution_capability_bridge.py").exists():
            services.append(
                ManagedService(
                    "opportunity_execution_capability_bridge",
                    (python, "-m", "companyos.runtime.opportunity_execution_capability_bridge", "run"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/closed_loop_outcome_evaluator.py").exists():
            services.append(
                ManagedService(
                    "closed_loop_outcome_evaluator",
                    (python, "-m", "companyos.runtime.closed_loop_outcome_evaluator", "run"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/autonomous_evidence_acquisition.py").exists():
            services.append(
                ManagedService(
                    "autonomous_evidence_acquisition",
                    (python, "-m", "companyos.runtime.autonomous_evidence_acquisition", "run"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/evidence_decision_closure.py").exists():
            services.append(
                ManagedService(
                    "evidence_decision_closure",
                    (python, "-m", "companyos.runtime.evidence_decision_closure", "run"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/profit_to_action_closure.py").exists():
            services.append(
                ManagedService(
                    "profit_to_action_closure",
                    (python, "-m", "companyos.runtime.profit_to_action_closure", "run"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/continuous_profit_improvement_loop.py").exists():
            services.append(
                ManagedService(
                    "continuous_profit_improvement_loop",
                    (python, "-m", "companyos.runtime.continuous_profit_improvement_loop"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/adaptive_worker_factory.py").exists():
            services.append(
                ManagedService(
                    "adaptive_worker_factory",
                    (python, "-m", "companyos.runtime.adaptive_worker_factory"),
                )
            )
        if (Path.home()/"companyos/companyos/runtime/adaptive_workforce_execution_bridge.py").exists():
            services.append(
                ManagedService(
                    "adaptive_workforce_execution_bridge",
                    (python, "-m", "companyos.runtime.adaptive_workforce_execution_bridge"),
                )
            )
        return services

    def _log(self, message: str) -> None:
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")

    def evaluate(self, services):
        actions = []
        for service in services or []:
            actions.append(
                {
                    "service": service.get("service"),
                    "action": "keep_running"
                    if service.get("healthy", False)
                    else "restart",
                }
            )
        return actions

    def _state(self) -> dict:
        services = {}
        for spec in self.services:
            child = self.children.get(spec.name)
            services[spec.name] = {
                "pid": child.pid if child else None,
                "running": bool(child and child.poll() is None),
                "returncode": None
                if not child or child.poll() is None
                else child.returncode,
                "restarts": self.restarts.get(spec.name, 0),
                "consecutive_failures": self.failures.get(spec.name, 0),
                "argv": list(spec.argv),
            }
        return {
            "running": not self._stopping,
            "supervisor_pid": os.getpid(),
            "started_at_unix": self.started_at,
            "updated_at_unix": time.time(),
            "stop_file": str(self.stop_path),
            "services": services,
        }

    def _write_state(self) -> None:
        tmp = self.state_path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(self._state(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.state_path)

    def _spawn(self, spec: ManagedService) -> None:
        env = os.environ.copy()
        root = str(self.root)
        current = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = root if not current else root + os.pathsep + current

        child = subprocess.Popen(
            list(spec.argv),
            cwd=self.root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self.children[spec.name] = child
        self.spawned_at[spec.name] = time.time()
        self._log(f"START service={spec.name} pid={child.pid}")

    def _ensure_running(self, spec: ManagedService) -> None:
        child = self.children.get(spec.name)
        if child and child.poll() is None:
            if time.time() - self.spawned_at.get(spec.name, self.started_at) >= max(10.0, self.poll_seconds * 2):
                self.failures[spec.name] = 0
            return

        if child is not None:
            rc = child.poll()
            self.failures[spec.name] = self.failures.get(spec.name, 0) + 1
            self.restarts[spec.name] = self.restarts.get(spec.name, 0) + 1
            delay = min(
                self.max_backoff,
                self.base_backoff * (2 ** min(self.failures[spec.name] - 1, 5)),
            )
            self._log(
                f"EXIT service={spec.name} returncode={rc} restart_in={delay:.1f}s"
            )
            time.sleep(delay)

        self._spawn(spec)

    def _terminate_child(
        self, name: str, child: subprocess.Popen, grace: float = 10.0
    ) -> None:
        if child.poll() is not None:
            return
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            return

        deadline = time.time() + grace
        while time.time() < deadline:
            if child.poll() is not None:
                return
            time.sleep(0.2)

        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        self._log(f"FORCE_KILL service={name} pid={child.pid}")

    # COMPANYOS_REQUEST_STOP_PID_TARGET_V26
    def request_stop(self) -> None:
        self.stop_path.write_text(f"pid={os.getpid()}\n", encoding="utf-8")

    # COMPANYOS_PID_TARGETED_STOP_V25
    def _targeted_stop_requested(self) -> bool:
        if not self.stop_path.exists():
            return False
        try:
            raw = self.stop_path.read_text(encoding="utf-8").strip()
            expected = f"pid={os.getpid()}"
            if raw == expected:
                return True
            stale = self.runtime_root / f"STOP_CONTINUOUS.stale.{int(time.time())}"
            try:
                self.stop_path.replace(stale)
            except Exception:
                self._clear_stop_file_for_start()
            self._log(f"IGNORED_STALE_STOP_REQUEST raw={raw!r}")
            return False
        except Exception as exc:
            self._log(f"STOP_REQUEST_READ_ERROR error={exc!r}")
            return False

    def run(self) -> int:
        self._lock_file = self.lock_path.open("a+")
        try:
            fcntl.flock(
                self._lock_file.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except BlockingIOError:
            self._log("SUPERVISOR_ALREADY_RUNNING")
            return 2

        self.stop_path.unlink(missing_ok=True)
        self._log(
            f"SUPERVISOR_START pid={os.getpid()} "
            f"services={[s.name for s in self.services]}"
        )

        def signal_handler(signum, _frame):
            self._log(f"SIGNAL signum={signum}")
            self._stopping = True

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        try:
            while not self._stopping and not self._targeted_stop_requested():
                for spec in self.services:
                    self._ensure_running(spec)
                self._write_state()
                time.sleep(self.poll_seconds)
        finally:
            self._stopping = True
            for name, child in list(self.children.items()):
                self._terminate_child(name, child)
            self._write_state()
            reason = "stop_file" if self.stop_path.exists() else "signal_or_exit"
            self._log(f"SUPERVISOR_STOP reason={reason}")

        return 0


def main() -> int:
    return ServiceSupervisor().run()


if __name__ == "__main__":
    raise SystemExit(main())
