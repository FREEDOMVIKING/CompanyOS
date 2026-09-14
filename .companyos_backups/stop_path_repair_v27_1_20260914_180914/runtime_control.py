from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any



# COMPANYOS_STOPFILE_LIFECYCLE_V23
def _clear_stop_file_for_start(self):
    candidates=[]
    for name in ("stop_file","stop_path","stop_request_path"):
        v=getattr(self,name,None)
        if v: candidates.append(Path(v))
    try: candidates.append(Path(self.runtime_root)/"STOP_CONTINUOUS")
    except Exception: pass
    removed=[]
    for pth in candidates:
        try:
            if pth.exists():
                pth.unlink(); removed.append(str(pth))
        except Exception: pass
    try:
        st=self.status()
        if isinstance(st,dict) and st.get("stop_requested"):
            st["stop_requested"]=False
            Path(self.state_path).write_text(json.dumps(st,indent=2)+"\n")
    except Exception: pass
    return {"removed_stop_files":removed}


class UnifiedRuntimeControl:
    _clear_stop_file_for_start = _clear_stop_file_for_start
    EXPECTED_SERVICES = {
        "continuous_goal_runtime",
        "productive_autonomy_watchdog",
        "local_dashboard",
        "profit_opportunity_runtime",
    }

    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime_root / "service_supervisor_state.json"
        # COMPANYOS_SUPERVISOR_DEDICATED_STOP_V27\n        self.stop_path = self.runtime_root / "SUPERVISOR_STOP"
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
            pid = int(pid)
            os.kill(pid, 0)
        except (ProcessLookupError, PermissionError, ValueError, TypeError):
            return False

        # Android/Termux can briefly leave a detached process as a zombie.
        # os.kill(pid, 0) still succeeds for zombies, so inspect /proc.
        try:
            stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
            right = stat.rsplit(")", 1)
            if len(right) == 2:
                state = right[1].strip().split()[0]
                if state in {"Z", "X", "x"}:
                    return False
        except Exception:
            pass

        return True

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
        self._clear_stop_file_for_start()
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

    def stop(self, wait_seconds: float = 45.0) -> dict[str, Any]:
        before = self.status()
        # COMPANYOS_PID_TARGETED_STOP_V24
        target_pid = before.get("supervisor_pid")
        if target_pid:
            self.stop_path.write_text(f"pid={int(target_pid)}\n", encoding="utf-8")
        else:
            self.stop_path.unlink(missing_ok=True)
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
