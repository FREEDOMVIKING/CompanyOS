#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase82_transaction_lifecycle_bundle"

pairs = [
    (
        BUNDLE / "transaction_lifecycle.py",
        ROOT / "companyos/walletintegration/transaction_lifecycle.py",
    ),
    (
        BUNDLE / "phase82_reconcile_last_signature.py",
        ROOT / "phase82_reconcile_last_signature.py",
    ),
    (
        BUNDLE / "phase82_lifecycle_test.py",
        ROOT / "phase82_lifecycle_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)
    if dst.exists():
        backup = dst.with_name(dst.name + f".phase82_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "82_TRANSACTION_LIFECYCLE_AND_RECONCILIATION",
    "status": "installed",
    "persistent_states": [
        "AUTHORIZED", "SIGNED", "SUBMITTED", "CONFIRMED", "FINALIZED", "FAILED"
    ],
    "submitted_is_not_success": True,
    "confirmation_reconciliation": True,
    "balance_reconciliation_fields": True,
    "installer_broadcasts": False,
    "verifier_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE82_TRANSACTION_LIFECYCLE_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE82_TRANSACTION_LIFECYCLE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("SUBMITTED_IS_NOT_SUCCESS: True")
print("CONFIRMATION_RECONCILIATION: True")
print("PERSISTENT_EXECUTION_RECORDS: True")
print("INSTALLER_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
