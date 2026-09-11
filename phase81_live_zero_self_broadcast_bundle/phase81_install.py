#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase81_live_zero_self_broadcast_bundle"

pairs = [
    (
        BUNDLE / "solana_confirmation_tracker.py",
        ROOT / "companyos/walletintegration/solana_confirmation_tracker.py",
    ),
    (
        BUNDLE / "phase81_manual_live_zero_self_test.py",
        ROOT / "phase81_manual_live_zero_self_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)
    if dst.exists():
        backup = dst.with_name(dst.name + f".phase81_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "81_LIVE_ZERO_SELF_BROADCAST",
    "status": "installed",
    "installer_broadcasts": False,
    "verifier_broadcasts": False,
    "manual_live_execution_required": True,
    "explicit_network_fee_confirmation_required": True,
    "value_transfer_lamports": 0,
    "network_fee_can_be_charged": True,
    "confirmation_tracking": "getSignatureStatuses",
    "balance_reconciliation": True,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE81_LIVE_ZERO_SELF_BROADCAST_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE81_LIVE_ZERO_SELF_BROADCAST: INSTALLED")
print("COMPILE_CHECK: PASS")
print("INSTALLER_BROADCASTS: False")
print("MANUAL_LIVE_EXECUTION_REQUIRED: True")
print("NETWORK_FEE_CAN_BE_CHARGED: True")
print("VALUE_TRANSFER_LAMPORTS: 0")
print("PRIVATE_KEY_PRINTED: False")
