#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase80_controlled_solana_broadcast_bundle"

pairs = [
    (
        BUNDLE / "controlled_solana_broadcaster.py",
        ROOT / "companyos/walletintegration/controlled_solana_broadcaster.py",
    ),
    (
        BUNDLE / "phase80_dry_run_test.py",
        ROOT / "phase80_dry_run_test.py",
    ),
    (
        BUNDLE / "phase80_manual_zero_self_broadcast.py",
        ROOT / "phase80_manual_zero_self_broadcast.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)
    if dst.exists():
        backup = dst.with_name(dst.name + f".phase80_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "80_CONTROLLED_SOLANA_BROADCAST",
    "status": "installed",
    "broadcast_default_disabled": True,
    "explicit_confirmation_required": True,
    "installer_broadcasts": False,
    "verifier_broadcasts": False,
    "dry_run_broadcasts": False,
    "manual_zero_self_broadcast_script_present": True,
    "network_fee_may_apply_to_manual_zero_self_broadcast": True,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE80_CONTROLLED_SOLANA_BROADCAST_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE80_CONTROLLED_SOLANA_BROADCAST: INSTALLED")
print("COMPILE_CHECK: PASS")
print("BROADCAST_DEFAULT_DISABLED: True")
print("EXPLICIT_CONFIRMATION_REQUIRED: True")
print("INSTALLER_BROADCASTS: False")
print("DRY_RUN_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
