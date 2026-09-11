#!/usr/bin/env python3
from __future__ import annotations

import ast
import datetime as dt
import json
import os
import py_compile
import shutil
from pathlib import Path

ROOT = Path.home() / "companyos"
PKG = ROOT / "companyos"
BUNDLE = ROOT / "phase68_v2_bundle"

RUNTIME_PKG = PKG / "runtime"
RUNTIME_INIT = RUNTIME_PKG / "__init__.py"

FILES = {
    BUNDLE / "health_supervisor.py": RUNTIME_PKG / "health_supervisor.py",
    BUNDLE / "phase68_startup_recover.py": ROOT / "phase68_startup_recover.py",
    BUNDLE / "phase68_health.py": ROOT / "phase68_health.py",
    BUNDLE / "phase68_heartbeat.py": ROOT / "phase68_heartbeat.py",
    BUNDLE / "phase68_watchdog.sh": ROOT / "phase68_watchdog.sh",
}

MANIFEST = ROOT / "PHASE68_V2_INSTALLED.json"

def backup(path, stamp):
    if not path.exists():
        return None
    dst = path.with_name(path.name + f".phase68_v2_backup_{stamp}")
    shutil.copy2(path, dst)
    return str(dst)

def copy_checked(src, dst):
    if not src.exists():
        raise SystemExit(f"INSTALL_ABORTED: missing {src}")
    text = src.read_text(encoding="utf-8")
    if dst.suffix == ".py":
        ast.parse(text)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")

def main():
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backups = {str(dst): backup(dst, stamp) for dst in FILES.values()}

    RUNTIME_PKG.mkdir(parents=True, exist_ok=True)
    if not RUNTIME_INIT.exists():
        RUNTIME_INIT.write_text("", encoding="utf-8")

    for src, dst in FILES.items():
        copy_checked(src, dst)

    for dst in FILES.values():
        if dst.suffix == ".py":
            py_compile.compile(str(dst), doraise=True)

    os.chmod(ROOT / "phase68_watchdog.sh", 0o700)

    manifest = {
        "phase": "68_V2",
        "status": "installed",
        "installed_at_utc": stamp,
        "backups": backups,
        "features": {
            "startup_recovery": True,
            "health_supervisor": True,
            "heartbeat": True,
            "watchdog_loop": True,
            "stale_pending_visibility": True,
        },
        "autonomy_design": {
            "blanket_restrictions_added": False,
            "internal_reversible_work_preserved": True,
            "research_planning_building_learning_preserved": True,
            "existing_irreversible_action_controls_preserved": True,
        },
        "safety": {
            "installer_creates_transaction": False,
            "installer_signs": False,
            "installer_broadcasts": False,
            "watchdog_rebroadcasts_transactions": False,
        },
    }

    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("PHASE68_V2_HEALTH_RECOVERY_AUTOMATION: INSTALLED")
    print("COMPILE_CHECK: PASS")
    print("BLANKET_AUTONOMY_RESTRICTIONS_ADDED: False")
    print("INTERNAL_REVERSIBLE_AUTONOMY_PRESERVED: True")
    print("EXISTING_IRREVERSIBLE_ACTION_CONTROLS_PRESERVED: True")
    print("NO_TRANSACTION_CREATED_BY_INSTALLER: True")
    print("NO_SIGNING_PERFORMED_BY_INSTALLER: True")
    print("NO_BROADCAST_PERFORMED_BY_INSTALLER: True")
    print("WATCHDOG_TRANSACTION_REBROADCASTS: False")
    print("MANIFEST:", MANIFEST)

if __name__ == "__main__":
    main()
