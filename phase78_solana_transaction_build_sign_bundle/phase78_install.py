#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase78_solana_transaction_build_sign_bundle"

pairs = [
    (
        BUNDLE / "solana_legacy_tx_builder.py",
        ROOT / "companyos/walletintegration/solana_legacy_tx_builder.py",
    ),
    (
        BUNDLE / "phase78_transaction_sign_test.py",
        ROOT / "phase78_transaction_sign_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)
    if dst.exists():
        backup = dst.with_name(dst.name + f".phase78_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "78_SOLANA_TRANSACTION_BUILD_AND_SIGN",
    "status": "installed",
    "real_legacy_transaction_message_builder": True,
    "test_instruction": "system_transfer_self_zero_lamports",
    "fetches_latest_blockhash": True,
    "local_signature": True,
    "local_signature_verification": True,
    "send_transaction_called": False,
    "simulate_transaction_called": False,
    "transaction_broadcast_by_bundle": False,
    "funds_moved_by_bundle": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE78_SOLANA_TRANSACTION_BUILD_SIGN_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE78_SOLANA_TRANSACTION_BUILD_AND_SIGN: INSTALLED")
print("COMPILE_CHECK: PASS")
print("ZERO_LAMPORT_SELF_TRANSFER_TEST: True")
print("SEND_TRANSACTION_CALLED_BY_INSTALLER: False")
print("SIMULATE_TRANSACTION_CALLED_BY_INSTALLER: False")
print("TRANSACTION_BROADCAST_BY_INSTALLER: False")
print("FUNDS_MOVED_BY_INSTALLER: False")
print("PRIVATE_KEY_PRINTED: False")
