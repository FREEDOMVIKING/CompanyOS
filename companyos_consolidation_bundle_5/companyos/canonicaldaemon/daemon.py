from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json, os, signal, time, traceback

from companyos.canonicalproduction import CanonicalProductionRuntime

class CanonicalCompanyOSDaemon:
    def __init__(self, companyos_root: str | None = None, heartbeat_interval: float = 15.0):
        self.root = Path(companyos_root or os.environ.get("COMPANYOS_ROOT", str(Path.home() / "companyos")))
        self.runtime = self.root / "companyos_runtime" / "canonical_daemon"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.heartbeat_file = self.runtime / "heartbeat.json"
        self.state_file = self.runtime / "state.json"
        self.pid_file = self.runtime / "daemon.pid"
        self.heartbeat_interval = heartbeat_interval
        self.stop_requested = False
        self.production = CanonicalProductionRuntime(str(self.root))

    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True))
        tmp.replace(path)

    def _signal(self, signum, frame):
        self.stop_requested = True

    def run_forever(self) -> int:
        signal.signal(signal.SIGTERM, self._signal)
        signal.signal(signal.SIGINT, self._signal)

        self.pid_file.write_text(str(os.getpid()))
        started = time.time()
        failures = 0

        self._write_json(self.state_file, {
            "running": True,
            "pid": os.getpid(),
            "started_at": started,
            "failures": failures,
        })

        try:
            status = self.production.start()

            while not self.stop_requested:
                try:
                    health = self.production.status()
                    heartbeat = {
                        "ts": time.time(),
                        "pid": os.getpid(),
                        "running": True,
                        "production_ready": bool(health.get("ready")),
                        "reason": health.get("reason"),
                        "broadcast_allowed": bool(
                            health.get("execution_gateway", {}).get("broadcast_allowed", False)
                        ),
                        "external_actions_allowed": bool(
                            health.get("execution_gateway", {}).get("external_actions_allowed", False)
                        ),
                        "failures": failures,
                    }
                    self._write_json(self.heartbeat_file, heartbeat)
                    time.sleep(self.heartbeat_interval)
                except Exception as e:
                    failures += 1
                    self._write_json(self.state_file, {
                        "running": True,
                        "pid": os.getpid(),
                        "started_at": started,
                        "failures": failures,
                        "last_error": repr(e),
                        "traceback": traceback.format_exc(),
                    })
                    time.sleep(min(30, 2 ** min(failures, 4)))

            return 0
        finally:
            try:
                self.production.stop()
            except Exception:
                pass

            self._write_json(self.state_file, {
                "running": False,
                "pid": os.getpid(),
                "started_at": started,
                "stopped_at": time.time(),
                "failures": failures,
            })

            try:
                if self.pid_file.exists() and self.pid_file.read_text().strip() == str(os.getpid()):
                    self.pid_file.unlink()
            except Exception:
                pass
