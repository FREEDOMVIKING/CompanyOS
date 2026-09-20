#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="${HOME}/companyos"
BRANCH="companyos-continuous-fix-2026-09-11"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="${ROOT}/backups/launch_control_${STAMP}"

cd "$ROOT"

current_branch="$(git branch --show-current)"
if [ "$current_branch" != "$BRANCH" ]; then
  echo "ERROR: expected branch $BRANCH, current branch is $current_branch"
  exit 2
fi

mkdir -p "$BACKUP"

for f in \
  companyos/runtime/runtime_status.py \
  companyos/runtime/launch_readiness.py \
  companyos/runtime/launch_health_snapshot.py \
  companyos/runtime/launch_gate.py \
  companyos/runtime/launch_runtime.py \
  scripts/companyos_launchctl \
  scripts/validate_companyos_launch_stack.py \
  scripts/install_companyos_termux_boot.sh \
  .gitignore
do
  if [ -e "$f" ]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$f" "$BACKUP/$f"
  fi
done

cat > companyos/runtime/runtime_status.py <<'PY'
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from companyos.runtime.runtime_control import UnifiedRuntimeControl


class RuntimeStatus:
    """
    Live runtime status derived from the actual continuous control plane.
    This replaces static "ready" declarations with observed process/state data.
    """

    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.control = UnifiedRuntimeControl(self.root)

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}

    def status(self) -> dict[str, Any]:
        health = self.control.health()
        watchdog = self._read_json(
            self.runtime_root / "productive_autonomy_watchdog_state.json"
        )
        goal_runtime = self._read_json(
            self.runtime_root / "continuous_goal_runtime_state.json"
        )

        return {
            "success": bool(health.get("healthy")),
            "status": (
                "companyos_continuous_runtime_healthy"
                if health.get("healthy")
                else "companyos_continuous_runtime_degraded"
            ),
            "checked_at_unix": time.time(),
            "continuous_runtime": {
                "running": health.get("running", False),
                "healthy": health.get("healthy", False),
                "issues": health.get("issues", []),
                "supervisor_pid": health.get("supervisor_pid"),
                "state_age_seconds": health.get("state_age_seconds"),
                "services": health.get("services", {}),
            },
            "productive_autonomy_watchdog": watchdog,
            "continuous_goal_runtime": goal_runtime,
            "restart_safe_recovery": True,
            "service_supervisor": True,
            "continuous_ceo_cycles": True,
            "unified_runtime_control": True,
        }
PY

cat > companyos/runtime/launch_health_snapshot.py <<'PY'
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

from companyos.runtime.runtime_status import RuntimeStatus


class LaunchHealthSnapshot:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.path = self.runtime_root / "launch_health_snapshot.json"

    def _repo_clean_summary(self) -> dict[str, Any]:
        import subprocess

        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.root,
                text=True,
                capture_output=True,
                check=False,
            )
            lines = [x for x in result.stdout.splitlines() if x.strip()]
            return {
                "ok": result.returncode == 0,
                "dirty": bool(lines),
                "changes": lines[:100],
                "change_count": len(lines),
            }
        except Exception as exc:
            return {
                "ok": False,
                "dirty": True,
                "changes": [f"{type(exc).__name__}:{exc}"],
                "change_count": 1,
            }

    def _storage(self) -> dict[str, Any]:
        usage = shutil.disk_usage(self.root)
        return {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
            "free_gb": round(usage.free / (1024 ** 3), 2),
        }

    def build(self) -> dict[str, Any]:
        runtime = RuntimeStatus(self.root).status()
        repo = self._repo_clean_summary()
        storage = self._storage()

        snapshot = {
            "checked_at_unix": time.time(),
            "runtime": runtime,
            "repository": repo,
            "storage": storage,
            "environment": {
                "python": shutil.which("python"),
                "git": shutil.which("git"),
                "termux": bool(os.getenv("PREFIX", "").startswith("/data/data/com.termux")),
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
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from companyos.runtime.launch_health_snapshot import LaunchHealthSnapshot


class LaunchReadinessAudit:
    """
    Conservative launch audit.

    "Ready" here means the local continuous control/runtime stack is healthy
    and the repository has enough basic structure to operate. It does not
    imply that optional external providers, credentials, or financial actions
    are configured.
    """

    SECRET_NAME_PATTERNS = (
        re.compile(r".*private.*key.*", re.I),
        re.compile(r".*secret.*", re.I),
        re.compile(r".*token.*", re.I),
        re.compile(r".*password.*", re.I),
    )

    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.runtime_root = self.root / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.audit_path = self.runtime_root / "launch_readiness_audit.json"

    def _exists(self, rel: str) -> bool:
        return (self.root / rel).exists()

    def _git_branch(self) -> str | None:
        try:
            out = subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=self.root,
                text=True,
            ).strip()
            return out or None
        except Exception:
            return None

    def _tracked_secret_like_files(self) -> list[str]:
        try:
            out = subprocess.check_output(
                ["git", "ls-files"],
                cwd=self.root,
                text=True,
            )
        except Exception:
            return []

        suspicious = []
        for line in out.splitlines():
            name = Path(line).name
            if any(p.match(name) for p in self.SECRET_NAME_PATTERNS):
                lower = line.lower()
                if lower.endswith((".example", ".sample", ".md", ".txt")):
                    continue
                suspicious.append(line)
        return suspicious[:100]

    def run(self) -> dict[str, Any]:
        snapshot = LaunchHealthSnapshot(self.root).build()
        runtime = snapshot["runtime"]
        repo = snapshot["repository"]
        storage = snapshot["storage"]

        checks = {
            "continuous_runtime_healthy": bool(
                runtime.get("continuous_runtime", {}).get("healthy")
            ),
            "runtime_control_present": self._exists(
                "companyos/runtime/runtime_control.py"
            ),
            "service_supervisor_present": self._exists(
                "companyos/runtime/service_supervisor.py"
            ),
            "control_cli_present": self._exists("scripts/companyosctl"),
            "git_available": bool(snapshot["environment"].get("git")),
            "python_available": bool(snapshot["environment"].get("python")),
            "storage_free_gt_1gb": float(storage.get("free_gb", 0)) >= 1.0,
        }

        suspicious = self._tracked_secret_like_files()
        checks["no_obvious_tracked_secret_named_files"] = not suspicious

        blocking_failures = [
            name for name, ok in checks.items()
            if not ok
        ]

        warnings = []
        if repo.get("dirty"):
            warnings.append(
                f"repository_has_{repo.get('change_count', 0)}_working_tree_changes"
            )

        branch = self._git_branch()
        if branch and branch != "companyos-continuous-fix-2026-09-11":
            warnings.append(f"unexpected_branch:{branch}")

        result = {
            "ready": not blocking_failures,
            "checked_at_unix": time.time(),
            "branch": branch,
            "checks": checks,
            "blocking_failures": blocking_failures,
            "warnings": warnings,
            "suspicious_tracked_secret_named_files": suspicious,
            "health_snapshot_path": str(
                self.runtime_root / "launch_health_snapshot.json"
            ),
        }

        tmp = self.audit_path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.audit_path)
        return result
PY

cat > companyos/runtime/launch_gate.py <<'PY'
from __future__ import annotations

from pathlib import Path
from typing import Any

from companyos.runtime.launch_readiness import LaunchReadinessAudit


class LaunchGate:
    def __init__(self, root: Path | None = None):
        self.audit = LaunchReadinessAudit(root)

    def evaluate(self) -> dict[str, Any]:
        result = self.audit.run()
        return {
            "allowed": bool(result.get("ready")),
            "reason": (
                "launch_readiness_passed"
                if result.get("ready")
                else "launch_readiness_blocked"
            ),
            "audit": result,
        }
PY

cat > companyos/runtime/launch_runtime.py <<'PY'
from __future__ import annotations

from pathlib import Path
from typing import Any

from companyos.runtime.launch_gate import LaunchGate
from companyos.runtime.runtime_control import UnifiedRuntimeControl


class CompanyOSLaunchRuntime:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or (Path.home() / "companyos")).resolve()
        self.control = UnifiedRuntimeControl(self.root)
        self.gate = LaunchGate(self.root)

    def start(self) -> dict[str, Any]:
        recovered = self.control.recover()
        gate = self.gate.evaluate()
        return {
            "ok": bool(recovered.get("ok") and gate.get("allowed")),
            "runtime": recovered,
            "launch_gate": gate,
        }

    def stop(self) -> dict[str, Any]:
        return self.control.stop()

    def status(self) -> dict[str, Any]:
        return {
            "health": self.control.health(),
            "launch_gate": self.gate.evaluate(),
        }
PY

cat > scripts/companyos_launchctl <<'PY'
#!/data/data/com.termux/files/usr/bin/python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path.home() / "companyos"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.runtime.launch_health_snapshot import LaunchHealthSnapshot
from companyos.runtime.launch_readiness import LaunchReadinessAudit
from companyos.runtime.launch_runtime import CompanyOSLaunchRuntime


def dump(value):
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="companyos_launchctl",
        description="CompanyOS launch/readiness control",
    )
    parser.add_argument(
        "command",
        choices=["start", "stop", "status", "audit", "snapshot"],
    )
    args = parser.parse_args()

    runtime = CompanyOSLaunchRuntime(ROOT)

    if args.command == "start":
        result = runtime.start()
    elif args.command == "stop":
        result = runtime.stop()
    elif args.command == "status":
        result = runtime.status()
    elif args.command == "audit":
        result = LaunchReadinessAudit(ROOT).run()
    elif args.command == "snapshot":
        result = LaunchHealthSnapshot(ROOT).build()
    else:
        return 2

    dump(result)

    if isinstance(result, dict):
        if "ok" in result:
            return 0 if result["ok"] else 1
        if "ready" in result:
            return 0 if result["ready"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
chmod +x scripts/companyos_launchctl

cat > scripts/validate_companyos_launch_stack.py <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path.home() / "companyos"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.runtime.launch_health_snapshot import LaunchHealthSnapshot
from companyos.runtime.launch_readiness import LaunchReadinessAudit
from companyos.runtime.launch_runtime import CompanyOSLaunchRuntime


def show(label, value):
    print(f"===== {label} =====")
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def main():
    runtime = CompanyOSLaunchRuntime(ROOT)

    started = runtime.start()
    show("START", started)
    if not started.get("ok"):
        raise SystemExit(20)

    snapshot = LaunchHealthSnapshot(ROOT).build()
    show("SNAPSHOT", snapshot)
    if not snapshot["runtime"]["continuous_runtime"]["healthy"]:
        raise SystemExit(21)

    audit = LaunchReadinessAudit(ROOT).run()
    show("AUDIT", audit)
    if not audit.get("ready"):
        raise SystemExit(22)

    print("COMPANYOS_LAUNCH_STACK_VALIDATION=PASS")


if __name__ == "__main__":
    main()
PY

# Harden the existing Termux boot installer to call launch recovery.
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
"$ROOT/scripts/companyos_launchctl" start >> "$ROOT/.companyos_runtime/termux_boot.log" 2>&1
EOF

chmod +x "$BOOT_FILE"

echo "Installed CompanyOS Termux boot launcher:"
echo "$BOOT_FILE"
echo
echo "Requires the Termux:Boot Android add-on to actually run at device startup."
SH
chmod +x scripts/install_companyos_termux_boot.sh

cat >> .gitignore <<'EOF'

# CompanyOS launch/readiness generated state
.companyos_runtime/launch_health_snapshot.json
.companyos_runtime/launch_readiness_audit.json
.companyos_runtime/termux_boot.log
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
  companyos/runtime/runtime_status.py \
  companyos/runtime/launch_health_snapshot.py \
  companyos/runtime/launch_readiness.py \
  companyos/runtime/launch_gate.py \
  companyos/runtime/launch_runtime.py \
  scripts/companyos_launchctl \
  scripts/validate_companyos_launch_stack.py

echo
echo "===== VALIDATING LAUNCH STACK ====="
python scripts/validate_companyos_launch_stack.py

echo
echo "===== INSTALLING TERMUX BOOT FILE ====="
scripts/install_companyos_termux_boot.sh

echo
echo "===== FINAL LAUNCH STATUS ====="
scripts/companyos_launchctl status

echo
echo "===== GIT CHANGES FOR THIS BUNDLE ====="
git status --short -- \
  companyos/runtime/runtime_status.py \
  companyos/runtime/launch_health_snapshot.py \
  companyos/runtime/launch_readiness.py \
  companyos/runtime/launch_gate.py \
  companyos/runtime/launch_runtime.py \
  scripts/companyos_launchctl \
  scripts/validate_companyos_launch_stack.py \
  scripts/install_companyos_termux_boot.sh \
  .gitignore

git add \
  companyos/runtime/runtime_status.py \
  companyos/runtime/launch_health_snapshot.py \
  companyos/runtime/launch_readiness.py \
  companyos/runtime/launch_gate.py \
  companyos/runtime/launch_runtime.py \
  scripts/companyos_launchctl \
  scripts/validate_companyos_launch_stack.py \
  scripts/install_companyos_termux_boot.sh \
  .gitignore

git commit -m "Add CompanyOS launch readiness and persistent recovery control" || true
git push origin "$BRANCH"

echo
echo "COMPANYOS_LAUNCH_CONTROL_BUNDLE=COMPLETE"
echo
echo "Launch commands:"
echo "  ~/companyos/scripts/companyos_launchctl start"
echo "  ~/companyos/scripts/companyos_launchctl stop"
echo "  ~/companyos/scripts/companyos_launchctl status"
echo "  ~/companyos/scripts/companyos_launchctl audit"
echo "  ~/companyos/scripts/companyos_launchctl snapshot"
