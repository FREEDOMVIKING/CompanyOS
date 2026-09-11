#!/usr/bin/env python3
from __future__ import annotations

import ast
import datetime as dt
import json
import py_compile
import shutil
from pathlib import Path

ROOT = Path.home() / "companyos"
PKG = ROOT / "companyos"
WALLET = PKG / "walletintegration"

SRC_WORKER = ROOT / "phase67_v2_bundle" / "reconciliation_worker.py"
SRC_STATUS = ROOT / "phase67_v2_bundle" / "phase67_v2_pending_status.py"
SRC_RUN = ROOT / "phase67_v2_bundle" / "phase67_v2_reconcile_once.py"

DST_WORKER = WALLET / "reconciliation_worker.py"
DST_STATUS = ROOT / "phase67_v2_pending_status.py"
DST_RUN = ROOT / "phase67_v2_reconcile_once.py"
MANIFEST = ROOT / "PHASE67_V2_INSTALLED.json"


def backup(path: Path, stamp: str):
    if not path.exists():
        return None
    dst = path.with_name(path.name + f".phase67_v2_backup_{stamp}")
    shutil.copy2(path, dst)
    return str(dst)


def copy_checked(src: Path, dst: Path):
    if not src.exists():
        raise SystemExit(f"INSTALL_ABORTED: missing {src}")
    text = src.read_text(encoding="utf-8")
    ast.parse(text)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def main():
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    backups = {
        "reconciliation_worker": backup(DST_WORKER, stamp),
        "pending_status_cli": backup(DST_STATUS, stamp),
        "reconcile_once_cli": backup(DST_RUN, stamp),
    }

    copy_checked(SRC_WORKER, DST_WORKER)
    copy_checked(SRC_STATUS, DST_STATUS)
    copy_checked(SRC_RUN, DST_RUN)

    py_compile.compile(str(DST_WORKER), doraise=True)
    py_compile.compile(str(DST_STATUS), doraise=True)
    py_compile.compile(str(DST_RUN), doraise=True)

    manifest = {
        "phase": "67_V2",
        "status": "installed",
        "installed_at_utc": stamp,
        "backups": backups,
        "features": {
            "restart_safe_reconciliation_worker": True,
            "pending_status_cli": True,
            "stale_pending_detection": True,
            "single_pass_reconciliation": True,
            "automatic_rebroadcast": False,
        },
        "safety": {
            "installer_creates_transaction": False,
            "installer_signs": False,
            "installer_broadcasts": False,
            "worker_creates_transaction": False,
            "worker_signs": False,
            "worker_rebroadcasts": False,
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("PHASE67_V2_RECONCILIATION_WORKER: INSTALLED")
    print("COMPILE_CHECK: PASS")
    print("NO_TRANSACTION_CREATED_BY_INSTALLER: True")
    print("NO_SIGNING_PERFORMED_BY_INSTALLER: True")
    print("NO_BROADCAST_PERFORMED_BY_INSTALLER: True")
    print("WORKER_REBROADCASTS: False")
    print("MANIFEST:", MANIFEST)


if __name__ == "__main__":
    main()
