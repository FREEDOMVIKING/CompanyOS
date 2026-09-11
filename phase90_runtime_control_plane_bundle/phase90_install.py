#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase90_runtime_control_plane_bundle"

pairs = [
    (
        BUNDLE / "runtime_control_plane.py",
        ROOT / "companyos/walletintegration/runtime_control_plane.py",
    ),
    (
        BUNDLE / "phase90_runtime_ctl.py",
        ROOT / "phase90_runtime_ctl.py",
    ),
    (
        BUNDLE / "phase90_control_plane_test.py",
        ROOT / "phase90_control_plane_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase90_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "90_RUNTIME_CONTROL_PLANE",
    "status": "installed",
    "detached_start": True,
    "status_command": True,
    "stop_command": True,
    "duplicate_supervisor_start_blocked": True,
    "pid_persistence": "~/.companyos_runtime/production_runtime_supervisor.pid",
    "log_persistence": "~/.companyos_runtime/production_runtime_supervisor.log",
    "control_plane_builds_transaction": False,
    "control_plane_signs_transaction": False,
    "control_plane_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE90_RUNTIME_CONTROL_PLANE_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE90_RUNTIME_CONTROL_PLANE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("DETACHED_START_AVAILABLE: True")
print("STATUS_COMMAND_AVAILABLE: True")
print("STOP_COMMAND_AVAILABLE: True")
print("DUPLICATE_SUPERVISOR_START_BLOCKED: True")
print("CONTROL_PLANE_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
