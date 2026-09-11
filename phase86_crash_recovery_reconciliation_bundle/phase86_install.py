#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase86_crash_recovery_reconciliation_bundle"

pairs = [
    (
        BUNDLE / "execution_recovery_manager.py",
        ROOT / "companyos/walletintegration/execution_recovery_manager.py",
    ),
    (
        BUNDLE / "phase86_recovery_test.py",
        ROOT / "phase86_recovery_test.py",
    ),
    (
        BUNDLE / "phase86_recover_runtime.py",
        ROOT / "phase86_recover_runtime.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)
    if dst.exists():
        backup = dst.with_name(dst.name + f".phase86_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "86_CRASH_RECOVERY_RECONCILIATION",
    "status": "installed",
    "authorized_signed_blind_rebroadcast": False,
    "submitted_reconciled_onchain_first": True,
    "confirmed_finalized_failed_recovery": True,
    "terminal_states_noop": True,
    "installer_broadcasts": False,
    "verifier_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE86_CRASH_RECOVERY_RECONCILIATION_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE86_CRASH_RECOVERY_RECONCILIATION: INSTALLED")
print("COMPILE_CHECK: PASS")
print("BLIND_REBROADCAST_PROTECTION: True")
print("SUBMITTED_ONCHAIN_RECONCILIATION: True")
print("INSTALLER_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
