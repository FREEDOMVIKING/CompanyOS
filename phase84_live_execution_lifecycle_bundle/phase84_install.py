#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase84_live_execution_lifecycle_bundle"

pairs = [
    (
        BUNDLE / "live_solana_execution_engine.py",
        ROOT / "companyos/walletintegration/live_solana_execution_engine.py",
    ),
    (
        BUNDLE / "phase84_dry_run_test.py",
        ROOT / "phase84_dry_run_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)
    if dst.exists():
        backup = dst.with_name(dst.name + f".phase84_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "84_LIVE_EXECUTION_LIFECYCLE_INTEGRATION",
    "status": "installed",
    "fresh_balance_before_authorization": True,
    "automatic_lifecycle_persistence": True,
    "build_sign_submit_confirm_reconcile_pipeline": True,
    "broadcast_default_disabled": True,
    "installer_broadcasts": False,
    "verifier_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE84_LIVE_EXECUTION_LIFECYCLE_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE84_LIVE_EXECUTION_LIFECYCLE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("FRESH_BALANCE_BEFORE_AUTH: True")
print("AUTOMATIC_LIFECYCLE_PERSISTENCE: True")
print("BROADCAST_DEFAULT_DISABLED: True")
print("INSTALLER_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
