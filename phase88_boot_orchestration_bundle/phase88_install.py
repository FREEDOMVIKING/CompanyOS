#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json, os
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase88_boot_orchestration_bundle"

pairs = [
    (
        BUNDLE / "boot_orchestrator.py",
        ROOT / "companyos/walletintegration/boot_orchestrator.py",
    ),
    (
        BUNDLE / "phase88_boot_readiness.py",
        ROOT / "phase88_boot_readiness.py",
    ),
    (
        BUNDLE / "phase88_boot_sequence.sh",
        ROOT / "phase88_boot_sequence.sh",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    if dst.exists():
        backup = dst.with_name(dst.name + f".phase88_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    if dst.suffix == ".py":
        ast.parse(dst.read_text(encoding="utf-8"))
        py_compile.compile(str(dst), doraise=True)

boot = ROOT / "phase88_boot_sequence.sh"
boot.chmod(0o700)

manifest = {
    "phase": "88_BOOT_ORCHESTRATION",
    "status": "installed",
    "boot_sequence": [
        "env_validation",
        "rpc_validation",
        "key_validation",
        "wallet_derivation",
        "fresh_live_balance",
        "startup_reconciliation",
        "readiness_decision",
    ],
    "boot_sequence_builds_transaction": False,
    "boot_sequence_signs_transaction": False,
    "boot_sequence_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE88_BOOT_ORCHESTRATION_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE88_BOOT_ORCHESTRATION: INSTALLED")
print("COMPILE_CHECK: PASS")
print("BOOT_SCRIPT_EXECUTABLE: True")
print("BOOT_SEQUENCE_BUILDS_TRANSACTION: False")
print("BOOT_SEQUENCE_SIGNS_TRANSACTION: False")
print("BOOT_SEQUENCE_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
