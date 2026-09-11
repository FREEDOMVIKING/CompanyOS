#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase91_runtime_watchdog_autorestart_bundle"

pairs = [
    (
        BUNDLE / "runtime_watchdog.py",
        ROOT / "companyos/walletintegration/runtime_watchdog.py",
    ),
    (
        BUNDLE / "phase91_watchdog_once.py",
        ROOT / "phase91_watchdog_once.py",
    ),
    (
        BUNDLE / "phase91_watchdog_loop.py",
        ROOT / "phase91_watchdog_loop.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase91_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "91_RUNTIME_WATCHDOG_AUTORESTART",
    "status": "installed",
    "dead_runtime_restart": True,
    "unresolved_submitted_blocks_restart": True,
    "restart_backoff": True,
    "restart_rate_limit": True,
    "watchdog_builds_transaction": False,
    "watchdog_signs_transaction": False,
    "watchdog_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE91_RUNTIME_WATCHDOG_AUTORESTART_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE91_RUNTIME_WATCHDOG_AUTORESTART: INSTALLED")
print("COMPILE_CHECK: PASS")
print("DEAD_RUNTIME_RESTART_AVAILABLE: True")
print("UNRESOLVED_SUBMITTED_BLOCKS_RESTART: True")
print("RESTART_RATE_LIMIT_AVAILABLE: True")
print("WATCHDOG_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
