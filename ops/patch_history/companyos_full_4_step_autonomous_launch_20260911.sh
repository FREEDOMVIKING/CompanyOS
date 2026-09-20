#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
BRANCH="companyos-continuous-fix-2026-09-11"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="${ROOT}/backups/full_autonomous_launch_${STAMP}"

cd "$ROOT"

CURRENT_BRANCH="$(git branch --show-current)"
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
  echo "ERROR: expected branch $BRANCH but current branch is $CURRENT_BRANCH"
  exit 2
fi

mkdir -p "$BACKUP"

FILES_TO_BACKUP=(
  companyos/runtime/service_supervisor.py
  companyos/runtime/runtime_control.py
  companyos/runtime/runtime_status.py
  companyos/runtime/launch_readiness.py
  companyos/runtime/launch_health_snapshot.py
  companyos/runtime/launch_gate.py
  companyos/runtime/launch_runtime.py
  companyos/runtime/dashboard_server.py
  companyos/runtime/connector_readiness.py
  companyos/runtime/end_to_end_qualification.py
  scripts/companyosctl
  scripts/companyos_launchctl
  scripts/companyos_dashboardctl
  scripts/companyos_connectorctl
  scripts/companyos_qualify
  scripts/install_companyos_termux_boot.sh
  scripts/validate_companyos_full_launch.py
  .gitignore
)

for f in "${FILES_TO_BACKUP[@]}"; do
  if [ -e "$f" ]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

echo "===== STEP 1/4: LAUNCH READINESS + RECOVERY ====="

cat > companyos/runtime/service_supervisor.py <<'PY'
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
    def __init__(self, services: Iterable[ManagedService] | None = None):
        self.root = (Path.home() / "companyos").resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)

        self.state_path = self.runtime_root / "service_supervisor_state.json"
        self.stop_path = self.runtime_root / "STOP_CONTINUOUS"
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
        self._stopping = False
        self._lock_file = None

    @staticmethod
    def default_services() -> list[ManagedService]:
        py = sys.executable
        return [
            ManagedService(
                "continuous_goal_runtime",
                (
                    py,
                    "-c",
                    "from companyos.runtime.continuous_goal_runtime "
                    "import ContinuousGoalRuntime; ContinuousGoalRuntime().run()",
                ),
            ),
            ManagedService(
                "productive_autonomy_watchdog",
                (py, "-m", "companyos.runtime.productive_autonomy_watchdog"),
            ),
            ManagedService(
                "local_dashboard",
                (py, "-m", "companyos.runtime.dashboard_server"),
            ),
        ]

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
        self._log(f"START service={spec.name} pid={child.pid}")

    def _ensure_running(self, spec: ManagedService) -> None:
        child = self.children.get(spec.name)
        if child and child.poll() is None:
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

    def request_stop(self) -> None:
        self.stop_path.write_text("stop\n", encoding="utf-8")

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
            while not self._stopping and not self.stop_path.exists():
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
PY

cat > companyos/runtime/runtime_control.py <<'PY'
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class UnifiedRuntimeControl:
    EXPECTED_SERVICES = {
        "continuous_goal_runtime",
        "productive_autonomy_watchdog",
        "local_dashboard",
    }

    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime_root / "service_supervisor_state.json"
        self.stop_path = self.runtime_root / "STOP_CONTINUOUS"
        self.pid_path = self.runtime_root / "service_supervisor.pid"
        self.control_log = self.runtime_root / "runtime_control.log"
        self.supervisor_log = self.runtime_root / "service_supervisor.log"

    def commands(self):
        return ["start", "stop", "restart", "status", "health", "recover", "logs"]

    @staticmethod
    def _pid_alive(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            os.kill(int(pid), 0)
            return True
        except (ProcessLookupError, PermissionError, ValueError, TypeError):
            return False

    def _log(self, message: str) -> None:
        with self.control_log.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}

    def _read_pid(self) -> int | None:
        try:
            return int(self.pid_path.read_text(encoding="utf-8").strip())
        except Exception:
            return None

    def status(self, queue_snapshot=None, heartbeat=None, watchdog=None):
        if queue_snapshot is not None or heartbeat is not None or watchdog is not None:
            watchdog = watchdog or {}
            return {
                "queue": queue_snapshot,
                "heartbeat": heartbeat,
                "watchdog": watchdog,
                "running": bool(watchdog.get("healthy")),
            }

        state = self._read_json(self.state_path)
        pid = int(state.get("supervisor_pid", 0) or 0) or self._read_pid()
        services = state.get("services") or {}
        normalized = {}
        all_children_running = True

        for name, raw in services.items():
            info = dict(raw or {})
            child_pid = int(info.get("pid", 0) or 0)
            alive = self._pid_alive(child_pid)
            running = bool(info.get("running")) and alive
            info["process_alive"] = alive
            info["running"] = running
            normalized[name] = info
            all_children_running = all_children_running and running

        expected_present = self.EXPECTED_SERVICES.issubset(set(normalized))
        supervisor_alive = self._pid_alive(pid)

        return {
            "running": bool(
                supervisor_alive
                and bool(state.get("running"))
                and expected_present
                and all_children_running
            ),
            "supervisor_pid": pid,
            "supervisor_alive": supervisor_alive,
            "expected_services_present": expected_present,
            "expected_services": sorted(self.EXPECTED_SERVICES),
            "stop_requested": self.stop_path.exists(),
            "updated_at_unix": state.get("updated_at_unix"),
            "services": normalized,
            "state_path": str(self.state_path),
        }

    def health(self, stale_after_seconds: float = 45.0) -> dict[str, Any]:
        status = self.status()
        now = time.time()
        updated = status.get("updated_at_unix")
        age = None
        if updated:
            try:
                age = max(0.0, now - float(updated))
            except Exception:
                age = None

        issues = []
        if not status["supervisor_alive"]:
            issues.append("supervisor_not_alive")
        if not status["expected_services_present"]:
            issues.append("expected_services_missing")
        for name in self.EXPECTED_SERVICES:
            if not status["services"].get(name, {}).get("running"):
                issues.append(f"{name}_not_running")
        if age is None or age > float(stale_after_seconds):
            issues.append("state_stale")
        if status["stop_requested"]:
            issues.append("stop_requested")

        return {
            **status,
            "healthy": not issues,
            "issues": issues,
            "state_age_seconds": None if age is None else round(age, 2),
            "checked_at_unix": now,
        }

    def start(self, wait_seconds: float = 15.0) -> dict[str, Any]:
        existing = self.health()
        if existing.get("healthy"):
            return {"ok": True, "action": "already_running", "health": existing}

        self.stop_path.unlink(missing_ok=True)
        log_handle = self.supervisor_log.open("a", encoding="utf-8")
        try:
            proc = subprocess.Popen(
                [sys.executable, "companyos/runtime/service_supervisor.py"],
                cwd=self.root,
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
                env=os.environ.copy(),
            )
        finally:
            log_handle.close()

        self.pid_path.write_text(f"{proc.pid}\n", encoding="utf-8")
        self._log(f"START requested pid={proc.pid}")

        deadline = time.time() + max(1.0, float(wait_seconds))
        last = None
        while time.time() < deadline:
            if proc.poll() is not None:
                return {
                    "ok": False,
                    "action": "start_failed",
                    "returncode": proc.returncode,
                    "health": self.health(),
                }
            last = self.health()
            if last.get("healthy"):
                return {
                    "ok": True,
                    "action": "started",
                    "pid": proc.pid,
                    "health": last,
                }
            time.sleep(0.5)

        return {
            "ok": bool(last and last.get("running")),
            "action": "start_timeout",
            "pid": proc.pid,
            "health": last or self.health(),
        }

    def stop(self, wait_seconds: float = 15.0) -> dict[str, Any]:
        before = self.status()
        self.stop_path.write_text("stop\n", encoding="utf-8")
        self._log("STOP requested")
        deadline = time.time() + max(1.0, float(wait_seconds))

        while time.time() < deadline:
            current = self.status()
            if not current.get("supervisor_alive"):
                self.pid_path.unlink(missing_ok=True)
                return {
                    "ok": True,
                    "action": "stopped",
                    "before": before,
                    "after": current,
                }
            time.sleep(0.5)

        pid = before.get("supervisor_pid")
        if self._pid_alive(pid):
            try:
                os.kill(int(pid), signal.SIGTERM)
            except ProcessLookupError:
                pass

        time.sleep(1.0)
        after = self.status()
        if not after.get("supervisor_alive"):
            self.pid_path.unlink(missing_ok=True)
        return {
            "ok": not after.get("supervisor_alive"),
            "action": "stopped_with_fallback"
            if not after.get("supervisor_alive")
            else "stop_timeout",
            "before": before,
            "after": after,
        }

    def restart(self) -> dict[str, Any]:
        stopped = self.stop()
        started = self.start()
        return {
            "ok": bool(stopped.get("ok") and started.get("ok")),
            "action": "restart",
            "stop": stopped,
            "start": started,
        }

    def recover(self) -> dict[str, Any]:
        health = self.health()
        if health.get("healthy"):
            return {"ok": True, "action": "no_recovery_needed", "health": health}
        if health.get("supervisor_alive"):
            result = self.restart()
            result["action"] = "restart_unhealthy_runtime"
            return result
        result = self.start()
        result["action"] = "start_missing_runtime"
        return result

    def logs(self, lines: int = 80) -> str:
        lines = max(1, min(int(lines), 1000))
        paths = [
            ("service_supervisor", self.supervisor_log),
            ("runtime_control", self.control_log),
            (
                "productive_autonomy_watchdog",
                self.runtime_root / "productive_autonomy_watchdog.log",
            ),
        ]
        out = []
        for name, path in paths:
            out.append(f"===== {name} =====")
            if not path.exists():
                out.append("(no log)")
                continue
            out.extend(
                path.read_text(encoding="utf-8", errors="replace").splitlines()[-lines:]
            )
        return "\n".join(out)
PY

cat > companyos/runtime/runtime_status.py <<'PY'
from __future__ import annotations

import json
import time
from pathlib import Path

from companyos.runtime.runtime_control import UnifiedRuntimeControl


class RuntimeStatus:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.control = UnifiedRuntimeControl(self.root)

    def _read(self, name: str):
        path = self.runtime_root / name
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}

    def status(self):
        health = self.control.health()
        return {
            "success": bool(health.get("healthy")),
            "status": "healthy" if health.get("healthy") else "degraded",
            "checked_at_unix": time.time(),
            "continuous_runtime": health,
            "continuous_goal_runtime": self._read(
                "continuous_goal_runtime_state.json"
            ),
            "productive_autonomy_watchdog": self._read(
                "productive_autonomy_watchdog_state.json"
            ),
        }
PY

cat > companyos/runtime/launch_health_snapshot.py <<'PY'
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from companyos.runtime.runtime_status import RuntimeStatus


class LaunchHealthSnapshot:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_root / "launch_health_snapshot.json"

    def build(self):
        usage = shutil.disk_usage(self.root)
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        changes = [x for x in result.stdout.splitlines() if x.strip()]

        snapshot = {
            "checked_at_unix": time.time(),
            "runtime": RuntimeStatus(self.root).status(),
            "repository": {
                "git_ok": result.returncode == 0,
                "dirty": bool(changes),
                "change_count": len(changes),
                "changes": changes[:100],
            },
            "storage": {
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "total_gb": round(usage.total / (1024 ** 3), 2),
            },
        }

        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)
        return snapshot
PY

cat > companyos/runtime/launch_readiness.py <<'PY'
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from companyos.runtime.launch_health_snapshot import LaunchHealthSnapshot


class LaunchReadinessAudit:
    """
    Blocks only on actual local runtime failures or clearly tracked credential
    file types. Security-related source code names such as token.py or
    secrets_policy.py are not treated as secrets.
    """

    BLOCKED_TRACKED_SUFFIXES = (
        ".pem",
        ".key",
        ".p12",
        ".pfx",
        ".secret",
    )

    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_root / "launch_readiness_audit.json"

    def _tracked_credential_files(self):
        try:
            files = subprocess.check_output(
                ["git", "ls-files"], cwd=self.root, text=True
            ).splitlines()
        except Exception:
            return []

        risky = []
        for rel in files:
            low = rel.lower()
            name = Path(low).name

            if name == ".env" or name.startswith(".env."):
                if name.endswith((".example", ".sample", ".template")):
                    continue
                risky.append(rel)
                continue

            if low.endswith(self.BLOCKED_TRACKED_SUFFIXES):
                risky.append(rel)
                continue

            if low.startswith("secrets/") and not low.endswith(
                (".md", ".txt", ".example", ".sample", ".template")
            ):
                risky.append(rel)

        return risky[:100]

    def run(self):
        snap = LaunchHealthSnapshot(self.root).build()
        runtime_health = snap["runtime"]["continuous_runtime"]
        tracked_creds = self._tracked_credential_files()

        checks = {
            "continuous_runtime_healthy": bool(runtime_health.get("healthy")),
            "service_supervisor_present": (
                self.root / "companyos/runtime/service_supervisor.py"
            ).exists(),
            "runtime_control_present": (
                self.root / "companyos/runtime/runtime_control.py"
            ).exists(),
            "storage_free_gt_1gb": float(snap["storage"]["free_gb"]) >= 1.0,
            "no_tracked_credential_files": not tracked_creds,
        }

        blocking = [name for name, ok in checks.items() if not ok]
        warnings = []
        if snap["repository"]["dirty"]:
            warnings.append(
                f"repository_has_{snap['repository']['change_count']}_working_tree_changes"
            )

        result = {
            "ready": not blocking,
            "checked_at_unix": time.time(),
            "checks": checks,
            "blocking_failures": blocking,
            "warnings": warnings,
            "tracked_credential_files": tracked_creds,
        }

        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)
        return result
PY

cat > companyos/runtime/launch_gate.py <<'PY'
from __future__ import annotations

from pathlib import Path
from companyos.runtime.launch_readiness import LaunchReadinessAudit


class LaunchGate:
    def __init__(self, root: Path | None = None):
        self.audit = LaunchReadinessAudit(root)

    def evaluate(self):
        audit = self.audit.run()
        return {
            "allowed": bool(audit.get("ready")),
            "reason": "launch_readiness_passed"
            if audit.get("ready")
            else "launch_readiness_blocked",
            "audit": audit,
        }
PY

cat > companyos/runtime/launch_runtime.py <<'PY'
from __future__ import annotations

from pathlib import Path

from companyos.runtime.launch_gate import LaunchGate
from companyos.runtime.runtime_control import UnifiedRuntimeControl


class CompanyOSLaunchRuntime:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.control = UnifiedRuntimeControl(self.root)
        self.gate = LaunchGate(self.root)

    def start(self):
        recovered = self.control.recover()
        gate = self.gate.evaluate()
        return {
            "ok": bool(recovered.get("ok") and gate.get("allowed")),
            "runtime": recovered,
            "launch_gate": gate,
        }

    def stop(self):
        return self.control.stop()

    def status(self):
        return {
            "health": self.control.health(),
            "launch_gate": self.gate.evaluate(),
        }
PY

echo "===== STEP 2/4: LIVE DASHBOARD + CONTROL PLANE ====="

cat > companyos/runtime/dashboard_server.py <<'PY'
from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = (Path.home() / "companyos").resolve()
RUNTIME = ROOT / ".companyos_runtime"
RUNTIME.mkdir(parents=True, exist_ok=True)

HOST = os.getenv("COMPANYOS_DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.getenv("COMPANYOS_DASHBOARD_PORT", "8765"))
TOKEN = os.getenv("COMPANYOS_DASHBOARD_TOKEN", "")

if HOST not in {"127.0.0.1", "localhost", "::1"} and not TOKEN:
    raise SystemExit(
        "Refusing non-local dashboard bind without COMPANYOS_DASHBOARD_TOKEN"
    )


def _json_bytes(obj):
    return json.dumps(obj, indent=2, sort_keys=True, default=str).encode("utf-8")


def _authorized(handler):
    if not TOKEN:
        return True
    supplied = handler.headers.get("X-CompanyOS-Token", "")
    return supplied == TOKEN


def _status():
    from companyos.runtime.runtime_control import UnifiedRuntimeControl
    from companyos.runtime.launch_readiness import LaunchReadinessAudit
    from companyos.runtime.connector_readiness import ConnectorReadinessAudit

    ctl = UnifiedRuntimeControl(ROOT)
    return {
        "checked_at_unix": time.time(),
        "health": ctl.health(),
        "launch_readiness": LaunchReadinessAudit(ROOT).run(),
        "connectors": ConnectorReadinessAudit(ROOT).run(),
    }


HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompanyOS Control</title>
<style>
body{font-family:system-ui;margin:18px;background:#111;color:#eee}
button{margin:4px;padding:12px 16px;font-size:16px}
pre{white-space:pre-wrap;background:#1d1d1d;padding:12px;border-radius:8px;overflow:auto}
.ok{color:#76e08a}.bad{color:#ff7c7c}
</style>
</head>
<body>
<h1>CompanyOS</h1>
<div>
<button onclick="act('start')">Start</button>
<button onclick="act('stop')">Stop</button>
<button onclick="act('restart')">Restart</button>
<button onclick="act('recover')">Recover</button>
<button onclick="refresh()">Refresh</button>
</div>
<h2 id="headline">Loading…</h2>
<pre id="out"></pre>
<script>
async function refresh(){
  const r=await fetch('/api/status');
  const j=await r.json();
  const healthy=!!(j.health&&j.health.healthy);
  document.getElementById('headline').innerHTML =
    healthy ? '<span class="ok">Runtime healthy</span>' :
              '<span class="bad">Runtime needs attention</span>';
  document.getElementById('out').textContent=JSON.stringify(j,null,2);
}
async function act(name){
  await fetch('/api/control/'+name,{method:'POST'});
  setTimeout(refresh,700);
}
refresh(); setInterval(refresh,5000);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "CompanyOSDashboard/1.0"

    def log_message(self, fmt, *args):
        path = RUNTIME / "dashboard_http.log"
        with path.open("a", encoding="utf-8") as f:
            f.write(
                f"{time.strftime('%Y-%m-%d %H:%M:%S')} "
                + (fmt % args)
                + "\n"
            )

    def _send_json(self, code, obj):
        data = _json_bytes(obj)
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            data = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path in {"/api/status", "/api/health"}:
            if not _authorized(self):
                self._send_json(401, {"ok": False, "error": "unauthorized"})
                return
            self._send_json(200, _status())
            return

        self._send_json(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        if not _authorized(self):
            self._send_json(401, {"ok": False, "error": "unauthorized"})
            return

        path = urlparse(self.path).path
        prefix = "/api/control/"
        if not path.startswith(prefix):
            self._send_json(404, {"ok": False, "error": "not_found"})
            return

        action = path[len(prefix):]
        from companyos.runtime.runtime_control import UnifiedRuntimeControl

        ctl = UnifiedRuntimeControl(ROOT)
        if action == "start":
            result = ctl.start()
        elif action == "stop":
            result = ctl.stop()
        elif action == "restart":
            result = ctl.restart()
        elif action == "recover":
            result = ctl.recover()
        else:
            self._send_json(
                400, {"ok": False, "error": f"unsupported_action:{action}"}
            )
            return

        self._send_json(200 if result.get("ok") else 500, result)


def main():
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    state = {
        "host": HOST,
        "port": PORT,
        "url": f"http://{HOST}:{PORT}/",
        "pid": os.getpid(),
        "started_at_unix": time.time(),
    }
    (RUNTIME / "dashboard_server_state.json").write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    httpd.serve_forever(poll_interval=0.5)


if __name__ == "__main__":
    main()
PY

echo "===== STEP 3/4: EXTERNAL CONNECTOR READINESS ====="

cat > companyos/runtime/connector_readiness.py <<'PY'
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path


class ConnectorReadinessAudit:
    """
    Non-destructive readiness audit. It never prints credential values and
    never sends money, email, deployments, or external writes.
    """

    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_root / "connector_readiness.json"

    @staticmethod
    def _env_any(*names):
        return any(bool(os.getenv(name, "").strip()) for name in names)

    def _files_matching(self, *keywords):
        matches = []
        lowered = tuple(k.lower() for k in keywords)
        for base in (
            self.root / "companyos",
            self.root / "connectors",
            self.root / "walletintegration",
        ):
            if not base.exists():
                continue
            for p in base.rglob("*.py"):
                s = str(p.relative_to(self.root)).lower()
                if any(k in s for k in lowered):
                    matches.append(str(p.relative_to(self.root)))
                    if len(matches) >= 30:
                        return matches
        return matches

    def _git_remote(self):
        try:
            remote = subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                cwd=self.root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            return {"configured": bool(remote), "remote": remote}
        except Exception:
            return {"configured": False, "remote": None}

    def run(self):
        openai_modules = self._files_matching("openai", "provider")
        hosting_modules = self._files_matching("vercel", "hosting", "deploy")
        email_modules = self._files_matching("smtp", "email", "communications")
        wallet_modules = self._files_matching("wallet", "solana", "treasury")

        connectors = {
            "openai": {
                "configured": self._env_any("OPENAI_API_KEY"),
                "adapter_code_present": bool(openai_modules),
                "modules": openai_modules[:8],
            },
            "hosting": {
                "configured": self._env_any(
                    "VERCEL_TOKEN",
                    "CLOUDFLARE_API_TOKEN",
                    "NETLIFY_AUTH_TOKEN",
                ),
                "adapter_code_present": bool(hosting_modules),
                "modules": hosting_modules[:8],
            },
            "email": {
                "configured": (
                    self._env_any("SMTP_HOST")
                    and self._env_any("SMTP_USERNAME", "SMTP_USER")
                    and self._env_any("SMTP_PASSWORD", "SMTP_PASS")
                ),
                "adapter_code_present": bool(email_modules),
                "modules": email_modules[:8],
            },
            "github": {
                **self._git_remote(),
                "adapter_code_present": True,
            },
            "solana_wallet": {
                "configured": (
                    self._env_any("SOLANA_RPC_URL", "RPC_URL")
                    and self._env_any(
                        "SOLANA_PRIVATE_KEY",
                        "PHANTOM_PRIVATE_KEY",
                        "WALLET_PRIVATE_KEY",
                    )
                ),
                "adapter_code_present": bool(wallet_modules),
                "modules": wallet_modules[:8],
                "live_finance_enabled": (
                    os.getenv("COMPANYOS_ENABLE_LIVE_FINANCE", "0") == "1"
                ),
            },
        }

        required_for_core = ["github"]
        core_external_ready = all(
            connectors[name]["configured"] for name in required_for_core
        )

        configured_count = sum(
            1 for value in connectors.values() if value.get("configured")
        )

        result = {
            "checked_at_unix": time.time(),
            "connectors": connectors,
            "configured_count": configured_count,
            "total_count": len(connectors),
            "core_external_ready": core_external_ready,
            "note": (
                "Unconfigured optional connectors do not block the local "
                "autonomous runtime. They block only the external actions "
                "that depend on them."
            ),
        }

        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)
        return result
PY

echo "===== STEP 4/4: END-TO-END QUALIFICATION ====="

cat > companyos/runtime/end_to_end_qualification.py <<'PY'
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

from companyos.runtime.connector_readiness import ConnectorReadinessAudit
from companyos.runtime.launch_readiness import LaunchReadinessAudit
from companyos.runtime.runtime_control import UnifiedRuntimeControl


class EndToEndQualification:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_root / "full_autonomous_qualification.json"
        self.control = UnifiedRuntimeControl(self.root)

    def _dashboard_check(self):
        url = "http://127.0.0.1:8765/api/health"
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                obj = json.loads(response.read().decode("utf-8"))
            return {
                "ok": response.status == 200,
                "url": url,
                "runtime_healthy": bool(
                    (obj.get("health") or {}).get("healthy")
                ),
            }
        except Exception as exc:
            return {
                "ok": False,
                "url": url,
                "error": f"{type(exc).__name__}:{exc}",
            }

    def run(self, recovery_test=True):
        start = self.control.recover()
        health_before = self.control.health()
        dashboard = self._dashboard_check()
        launch = LaunchReadinessAudit(self.root).run()
        connectors = ConnectorReadinessAudit(self.root).run()

        recovery = {"tested": False, "ok": None}
        if recovery_test:
            recovery["tested"] = True
            stopped = self.control.stop(wait_seconds=15)
            restarted = self.control.recover()
            health_after = self.control.health()
            recovery.update(
                {
                    "ok": bool(
                        stopped.get("ok")
                        and restarted.get("ok")
                        and health_after.get("healthy")
                    ),
                    "stop": {"ok": stopped.get("ok"), "action": stopped.get("action")},
                    "restart": {
                        "ok": restarted.get("ok"),
                        "action": restarted.get("action"),
                    },
                    "health_after": health_after,
                }
            )
        else:
            health_after = self.control.health()

        core_checks = {
            "runtime_started": bool(start.get("ok")),
            "runtime_healthy": bool(health_before.get("healthy")),
            "dashboard_reachable": bool(dashboard.get("ok")),
            "launch_readiness": bool(launch.get("ready")),
            "recovery_passed": bool(recovery.get("ok"))
            if recovery_test
            else True,
        }

        core_pass = all(core_checks.values())
        configured = connectors.get("configured_count", 0)
        total = connectors.get("total_count", 0)
        live_finance = (
            connectors.get("connectors", {})
            .get("solana_wallet", {})
            .get("live_finance_enabled", False)
        )

        if core_pass and configured == total and live_finance:
            launch_level = "full_external_autonomy_configured"
        elif core_pass:
            launch_level = "core_autonomy_ready_external_connectors_partial"
        else:
            launch_level = "not_ready"

        result = {
            "qualified_at_unix": time.time(),
            "core_pass": core_pass,
            "launch_level": launch_level,
            "core_checks": core_checks,
            "dashboard": dashboard,
            "launch_readiness": launch,
            "connectors": connectors,
            "recovery": recovery,
            "final_health": health_after,
            "important": (
                "This qualification proves the continuous local CompanyOS "
                "control/recovery/dashboard stack. External actions are only "
                "available for connectors reported configured. Live financial "
                "execution remains gated by COMPANYOS_ENABLE_LIVE_FINANCE=1."
            ),
        }

        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)
        return result
PY

cat > scripts/companyosctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path.home() / "companyos"
sys.path.insert(0, str(ROOT))
from companyos.runtime.runtime_control import UnifiedRuntimeControl

def dump(x): print(json.dumps(x, indent=2, sort_keys=True, default=str))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command", choices=["start","stop","restart","status","health","recover","logs"])
    p.add_argument("--lines", type=int, default=80)
    a=p.parse_args()
    c=UnifiedRuntimeControl(ROOT)
    if a.command=="start": r=c.start()
    elif a.command=="stop": r=c.stop()
    elif a.command=="restart": r=c.restart()
    elif a.command=="status": r=c.status()
    elif a.command=="health": r=c.health()
    elif a.command=="recover": r=c.recover()
    else:
        print(c.logs(a.lines)); return 0
    dump(r)
    if isinstance(r,dict):
        if "ok" in r: return 0 if r["ok"] else 1
        if "healthy" in r: return 0 if r["healthy"] else 1
    return 0

if __name__=="__main__": raise SystemExit(main())
PY
chmod +x scripts/companyosctl

cat > scripts/companyos_launchctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT=Path.home()/"companyos"
sys.path.insert(0,str(ROOT))
from companyos.runtime.launch_runtime import CompanyOSLaunchRuntime
from companyos.runtime.launch_readiness import LaunchReadinessAudit
from companyos.runtime.launch_health_snapshot import LaunchHealthSnapshot

def dump(x): print(json.dumps(x,indent=2,sort_keys=True,default=str))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command", choices=["start","stop","status","audit","snapshot"])
    a=p.parse_args()
    r=CompanyOSLaunchRuntime(ROOT)
    if a.command=="start": out=r.start()
    elif a.command=="stop": out=r.stop()
    elif a.command=="status": out=r.status()
    elif a.command=="audit": out=LaunchReadinessAudit(ROOT).run()
    else: out=LaunchHealthSnapshot(ROOT).build()
    dump(out)
    if "ok" in out: return 0 if out["ok"] else 1
    if "ready" in out: return 0 if out["ready"] else 1
    return 0

if __name__=="__main__": raise SystemExit(main())
PY
chmod +x scripts/companyos_launchctl

cat > scripts/companyos_dashboardctl <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${HOME}/companyos"
case "${1:-status}" in
  url)
    echo "http://127.0.0.1:${COMPANYOS_DASHBOARD_PORT:-8765}/"
    ;;
  status)
    python - <<'PY'
import json, urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=5) as r:
        print(json.dumps(json.loads(r.read().decode()),indent=2,sort_keys=True))
except Exception as e:
    print("dashboard unavailable:", type(e).__name__, e)
    raise SystemExit(1)
PY
    ;;
  *)
    echo "Usage: $0 [status|url]"
    exit 2
    ;;
esac
SH
chmod +x scripts/companyos_dashboardctl

cat > scripts/companyos_connectorctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path.home()/"companyos"
sys.path.insert(0,str(ROOT))
from companyos.runtime.connector_readiness import ConnectorReadinessAudit
print(json.dumps(ConnectorReadinessAudit(ROOT).run(),indent=2,sort_keys=True))
PY
chmod +x scripts/companyos_connectorctl

cat > scripts/companyos_qualify <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path.home()/"companyos"
sys.path.insert(0,str(ROOT))
from companyos.runtime.end_to_end_qualification import EndToEndQualification
result=EndToEndQualification(ROOT).run(recovery_test=True)
print(json.dumps(result,indent=2,sort_keys=True,default=str))
raise SystemExit(0 if result.get("core_pass") else 1)
PY
chmod +x scripts/companyos_qualify

cat > scripts/install_companyos_termux_boot.sh <<'SH'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="${HOME}/companyos"
BOOT_DIR="${HOME}/.termux/boot"
BOOT_FILE="${BOOT_DIR}/start-companyos"
mkdir -p "$BOOT_DIR"
cat > "$BOOT_FILE" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
cd "$ROOT"
mkdir -p "$ROOT/.companyos_runtime"
"$ROOT/scripts/companyosctl" recover >> "$ROOT/.companyos_runtime/termux_boot.log" 2>&1
EOF
chmod +x "$BOOT_FILE"
echo "Installed: $BOOT_FILE"
echo "Termux:Boot Android add-on is required for Android boot execution."
SH
chmod +x scripts/install_companyos_termux_boot.sh

cat > scripts/validate_companyos_full_launch.py <<'PY'
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path.home()/"companyos"
sys.path.insert(0,str(ROOT))
from companyos.runtime.end_to_end_qualification import EndToEndQualification

result=EndToEndQualification(ROOT).run(recovery_test=True)
print(json.dumps(result,indent=2,sort_keys=True,default=str))
if not result.get("core_pass"):
    raise SystemExit(40)
print("COMPANYOS_FULL_4_STEP_CORE_VALIDATION=PASS")
PY

cat >> .gitignore <<'EOF'

# CompanyOS full autonomous launch generated state
.companyos_runtime/
*.sqlite3-journal
*.sqlite3-shm
*.sqlite3-wal
companyos/runtime/*.bak*
companyos/runtime/*.backup
companyos/runtime/*.candidate*
EOF

python - <<'PY'
from pathlib import Path
p=Path(".gitignore")
seen=set()
out=[]
for line in p.read_text(encoding="utf-8").splitlines():
    if line.strip() and line in seen:
        continue
    if line.strip():
        seen.add(line)
    out.append(line)
p.write_text("\n".join(out).rstrip()+"\n",encoding="utf-8")
PY

echo
echo "===== COMPILING ALL NEW CORE FILES ====="
python -m py_compile \
  companyos/runtime/service_supervisor.py \
  companyos/runtime/runtime_control.py \
  companyos/runtime/runtime_status.py \
  companyos/runtime/launch_health_snapshot.py \
  companyos/runtime/launch_readiness.py \
  companyos/runtime/launch_gate.py \
  companyos/runtime/launch_runtime.py \
  companyos/runtime/dashboard_server.py \
  companyos/runtime/connector_readiness.py \
  companyos/runtime/end_to_end_qualification.py \
  scripts/companyosctl \
  scripts/companyos_launchctl \
  scripts/companyos_connectorctl \
  scripts/companyos_qualify \
  scripts/validate_companyos_full_launch.py

echo
echo "===== RESETTING OLD SUPERVISOR STACK ====="
scripts/companyosctl stop >/dev/null 2>&1 || true
sleep 2

echo
echo "===== INSTALLING TERMUX BOOT RECOVERY ====="
scripts/install_companyos_termux_boot.sh

echo
echo "===== RUNNING COMPLETE 4-STEP QUALIFICATION ====="
python scripts/validate_companyos_full_launch.py

echo
echo "===== CONNECTOR READINESS ====="
scripts/companyos_connectorctl

echo
echo "===== DASHBOARD URL ====="
scripts/companyos_dashboardctl url

echo
echo "===== STAGING ONLY THIS BUILD ====="
git add \
  companyos/runtime/service_supervisor.py \
  companyos/runtime/runtime_control.py \
  companyos/runtime/runtime_status.py \
  companyos/runtime/launch_health_snapshot.py \
  companyos/runtime/launch_readiness.py \
  companyos/runtime/launch_gate.py \
  companyos/runtime/launch_runtime.py \
  companyos/runtime/dashboard_server.py \
  companyos/runtime/connector_readiness.py \
  companyos/runtime/end_to_end_qualification.py \
  scripts/companyosctl \
  scripts/companyos_launchctl \
  scripts/companyos_dashboardctl \
  scripts/companyos_connectorctl \
  scripts/companyos_qualify \
  scripts/install_companyos_termux_boot.sh \
  scripts/validate_companyos_full_launch.py \
  .gitignore

git commit -m "Complete four-step CompanyOS autonomous launch stack" || true
git push origin "$BRANCH"

echo
echo "===== FINAL HEALTH ====="
scripts/companyosctl health

echo
echo "===== FINAL QUALIFICATION SUMMARY ====="
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos/.companyos_runtime/full_autonomous_qualification.json"
obj=json.loads(p.read_text())
print("core_pass:", obj.get("core_pass"))
print("launch_level:", obj.get("launch_level"))
print("core_checks:", obj.get("core_checks"))
c=obj.get("connectors",{})
print("connectors_configured:", c.get("configured_count"), "/", c.get("total_count"))
print("dashboard:", obj.get("dashboard"))
PY

echo
echo "COMPANYOS_FULL_4_STEP_BUILD=COMPLETE"
echo "Dashboard: http://127.0.0.1:8765/"
echo
echo "Control commands:"
echo "  ~/companyos/scripts/companyosctl start"
echo "  ~/companyos/scripts/companyosctl stop"
echo "  ~/companyos/scripts/companyosctl restart"
echo "  ~/companyos/scripts/companyosctl health"
echo "  ~/companyos/scripts/companyos_launchctl audit"
echo "  ~/companyos/scripts/companyos_connectorctl"
echo "  ~/companyos/scripts/companyos_qualify"
