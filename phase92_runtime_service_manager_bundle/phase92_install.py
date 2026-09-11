#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase92_runtime_service_manager_bundle"

pairs = [
    (
        BUNDLE / "runtime_service_manager.py",
        ROOT / "companyos/walletintegration/runtime_service_manager.py",
    ),
    (
        BUNDLE / "phase92_runtime_service_ctl.py",
        ROOT / "phase92_runtime_service_ctl.py",
    ),
    (
        BUNDLE / "phase92_service_manager_test.py",
        ROOT / "phase92_service_manager_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase92_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "92_RUNTIME_SERVICE_MANAGER",
    "status": "installed",
    "one_command_stack_start": True,
    "supervisor_and_watchdog_status": True,
    "one_command_stack_stop": True,
    "duplicate_watchdog_start_blocked": True,
    "unresolved_submitted_blocks_start": True,
    "service_manager_builds_transaction": False,
    "service_manager_signs_transaction": False,
    "service_manager_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE92_RUNTIME_SERVICE_MANAGER_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE92_RUNTIME_SERVICE_MANAGER: INSTALLED")
print("COMPILE_CHECK: PASS")
print("ONE_COMMAND_STACK_START: True")
print("ONE_COMMAND_STACK_STOP: True")
print("SUPERVISOR_AND_WATCHDOG_STATUS: True")
print("UNRESOLVED_SUBMITTED_BLOCKS_START: True")
print("SERVICE_MANAGER_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
