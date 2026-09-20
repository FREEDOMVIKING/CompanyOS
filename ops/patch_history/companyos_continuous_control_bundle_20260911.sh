#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
BRANCH="companyos-continuous-fix-2026-09-11"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="${ROOT}/backups/continuous_control_${STAMP}"

cd "$ROOT"

current_branch="$(git branch --show-current)"
if [ "$current_branch" != "$BRANCH" ]; then
  echo "ERROR: expected branch $BRANCH, current branch is $current_branch"
  exit 2
fi

mkdir -p "$BACKUP"
for f in \
  companyos/runtime/runtime_control.py \
  scripts/companyosctl \
  scripts/install_companyos_termux_boot.sh \
  scripts/validate_companyos_continuous.py \
  .gitignore
do
  if [ -e "$f" ]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

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
    """
    Concrete control plane for the CompanyOS continuous runtime.

    It controls one service_supervisor process. The supervisor owns the
    continuous goal runtime and productive autonomy watchdog child processes.
    """

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
        return [
            "start",
            "stop",
            "restart",
            "status",
            "health",
            "recover",
            "logs",
        ]

    def _log(self, message: str) -> None:
        with self.control_log.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")

    @staticmethod
    def _pid_alive(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            os.kill(int(pid), 0)
            return True
        except (ProcessLookupError, PermissionError, ValueError, TypeError):
            return False

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

    def _state(self) -> dict[str, Any]:
        return self._read_json(self.state_path)

    def status(self, queue_snapshot=None, heartbeat=None, watchdog=None):
        # Compatibility path for older callers.
        if queue_snapshot is not None or heartbeat is not None or watchdog is not None:
            watchdog = watchdog or {}
            return {
                "queue": queue_snapshot,
                "heartbeat": heartbeat,
                "watchdog": watchdog,
                "running": bool(watchdog.get("healthy")),
            }

        state = self._state()
        pid = int(state.get("supervisor_pid", 0) or 0) or self._read_pid()
        services = state.get("services") or {}

        normalized = {}
        all_children_running = True

        for name, info in services.items():
            info = dict(info or {})
            child_pid = int(info.get("pid", 0) or 0)
            process_alive = self._pid_alive(child_pid)
            declared_running = bool(info.get("running", False))
            running = declared_running and process_alive
            info["process_alive"] = process_alive
            info["running"] = running
            normalized[name] = info
            all_children_running = all_children_running and running

        expected = {"continuous_goal_runtime", "productive_autonomy_watchdog"}
        expected_present = expected.issubset(set(normalized))
        supervisor_alive = self._pid_alive(pid)
        declared_supervisor_running = bool(state.get("running", False))

        return {
            "running": bool(
                supervisor_alive
                and declared_supervisor_running
                and expected_present
                and all_children_running
            ),
            "supervisor_pid": pid,
            "supervisor_alive": supervisor_alive,
            "expected_services_present": expected_present,
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

        stale = age is None or age > float(stale_after_seconds)
        issues = []

        if not status["supervisor_alive"]:
            issues.append("supervisor_not_alive")
        if not status["expected_services_present"]:
            issues.append("expected_services_missing")
        for name, info in status["services"].items():
            if not info.get("running"):
                issues.append(f"{name}_not_running")
        if stale:
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

    def start(self, wait_seconds: float = 12.0) -> dict[str, Any]:
        existing = self.health()
        if existing.get("healthy"):
            return {
                "ok": True,
                "action": "already_running",
                "health": existing,
            }

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
        last_health = None

        while time.time() < deadline:
            if proc.poll() is not None:
                last_health = self.health()
                return {
                    "ok": False,
                    "action": "start_failed",
                    "returncode": proc.returncode,
                    "health": last_health,
                }

            last_health = self.health()
            if last_health.get("healthy"):
                return {
                    "ok": True,
                    "action": "started",
                    "pid": proc.pid,
                    "health": last_health,
                }
            time.sleep(0.5)

        return {
            "ok": bool(last_health and last_health.get("running")),
            "action": "start_timeout",
            "pid": proc.pid,
            "health": last_health or self.health(),
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
                self._log(f"STOP fallback SIGTERM pid={pid}")
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
            return {
                "ok": True,
                "action": "no_recovery_needed",
                "health": health,
            }

        if health.get("supervisor_alive"):
            result = self.restart()
            result["action"] = "restart_unhealthy_runtime"
            return result

        result = self.start()
        result["action"] = "start_missing_runtime"
        return result

    def logs(self, lines: int = 80) -> str:
        lines = max(1, min(int(lines), 1000))
        sources = [
            ("service_supervisor", self.supervisor_log),
            ("runtime_control", self.control_log),
            (
                "productive_autonomy_watchdog",
                self.runtime_root / "productive_autonomy_watchdog.log",
            ),
        ]

        output = []
        for name, path in sources:
            output.append(f"===== {name} =====")
            if not path.exists():
                output.append("(no log)")
                continue
            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ).splitlines()
                output.extend(content[-lines:])
            except Exception as exc:
                output.append(f"(error reading log: {type(exc).__name__}: {exc})")
        return "\n".join(output)
PY

cat > scripts/companyosctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path.home() / "companyos"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.runtime.runtime_control import UnifiedRuntimeControl


def print_json(value):
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="companyosctl",
        description="CompanyOS continuous runtime control",
    )
    parser.add_argument(
        "command",
        choices=[
            "start",
            "stop",
            "restart",
            "status",
            "health",
            "recover",
            "logs",
        ],
    )
    parser.add_argument("--lines", type=int, default=80)
    args = parser.parse_args()

    control = UnifiedRuntimeControl()

    if args.command == "start":
        result = control.start()
    elif args.command == "stop":
        result = control.stop()
    elif args.command == "restart":
        result = control.restart()
    elif args.command == "status":
        result = control.status()
    elif args.command == "health":
        result = control.health()
    elif args.command == "recover":
        result = control.recover()
    elif args.command == "logs":
        print(control.logs(args.lines))
        return 0
    else:
        parser.error("unsupported command")
        return 2

    print_json(result)
    return 0 if result.get("ok", result.get("healthy", False)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod +x scripts/companyosctl

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

echo "Installed CompanyOS Termux boot launcher:"
echo "$BOOT_FILE"
echo
echo "This file will be used by Termux:Boot when that Android add-on is installed"
echo "and allowed to run at device startup."
SH
chmod +x scripts/install_companyos_termux_boot.sh

cat > scripts/validate_companyos_continuous.py <<'PY'
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.runtime.runtime_control import UnifiedRuntimeControl


def dump(label, value):
    print(f"===== {label} =====")
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def main():
    ctl = UnifiedRuntimeControl()

    ctl.stop(wait_seconds=5)
    ctl.stop_path.unlink(missing_ok=True)

    started = ctl.start(wait_seconds=15)
    dump("START", started)
    if not started.get("ok"):
        raise SystemExit(10)

    health = ctl.health(stale_after_seconds=45)
    dump("HEALTH", health)
    if not health.get("healthy"):
        raise SystemExit(11)

    first_pid = health.get("supervisor_pid")
    second = ctl.start(wait_seconds=2)
    dump("DUPLICATE START", second)
    second_pid = (second.get("health") or {}).get("supervisor_pid")
    if second.get("action") != "already_running":
        raise SystemExit(12)
    if first_pid != second_pid:
        raise SystemExit(13)

    stopped = ctl.stop(wait_seconds=15)
    dump("STOP", stopped)
    if not stopped.get("ok"):
        raise SystemExit(14)

    time.sleep(1)
    final = ctl.status()
    dump("FINAL", final)
    if final.get("supervisor_alive"):
        raise SystemExit(15)

    print("COMPANYOS_CONTINUOUS_VALIDATION=PASS")


if __name__ == "__main__":
    main()
PY

# Extend ignore rules without removing the user's existing rules.
cat >> .gitignore <<'EOF'

# CompanyOS continuous runtime generated control files
.companyos_runtime/*.pid
.companyos_runtime/*.lock
.companyos_runtime/*.tmp
companyos/runtime/*.bak*
companyos/runtime/*.candidate*
companyos/runtime/*.backup
*.sqlite3-journal
*.sqlite3-shm
*.sqlite3-wal
EOF

python - <<'PY'
from pathlib import Path

p = Path(".gitignore")
seen = set()
out = []
for line in p.read_text(encoding="utf-8").splitlines():
    if line in seen and line.strip():
        continue
    seen.add(line)
    out.append(line)
p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
PY

python -m py_compile \
  companyos/runtime/service_supervisor.py \
  companyos/runtime/runtime_control.py \
  scripts/companyosctl \
  scripts/validate_companyos_continuous.py

echo
echo "===== RUNNING CONTINUOUS VALIDATION ====="
python scripts/validate_companyos_continuous.py

echo
echo "===== INSTALLING OPTIONAL TERMUX BOOT LAUNCHER ====="
scripts/install_companyos_termux_boot.sh

echo
echo "===== GIT CHANGES FOR THIS BUNDLE ====="
git status --short -- \
  companyos/runtime/runtime_control.py \
  scripts/companyosctl \
  scripts/install_companyos_termux_boot.sh \
  scripts/validate_companyos_continuous.py \
  .gitignore

git add \
  companyos/runtime/runtime_control.py \
  scripts/companyosctl \
  scripts/install_companyos_termux_boot.sh \
  scripts/validate_companyos_continuous.py \
  .gitignore

git commit -m "Add unified continuous CompanyOS control and recovery" || true
git push origin "$BRANCH"

echo
echo "===== FINAL HEALTH ====="
scripts/companyosctl start
scripts/companyosctl health

echo
echo "COMPANYOS_CONTINUOUS_CONTROL_BUNDLE=COMPLETE"
echo
echo "Commands:"
echo "  ~/companyos/scripts/companyosctl start"
echo "  ~/companyos/scripts/companyosctl stop"
echo "  ~/companyos/scripts/companyosctl restart"
echo "  ~/companyos/scripts/companyosctl status"
echo "  ~/companyos/scripts/companyosctl health"
echo "  ~/companyos/scripts/companyosctl recover"
echo "  ~/companyos/scripts/companyosctl logs"
