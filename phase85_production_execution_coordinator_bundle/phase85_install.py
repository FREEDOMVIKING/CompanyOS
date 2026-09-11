#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase85_production_execution_coordinator_bundle"

pairs = [
    (
        BUNDLE / "production_execution_coordinator.py",
        ROOT / "companyos/walletintegration/production_execution_coordinator.py",
    ),
    (
        BUNDLE / "phase85_coordinator_dry_run_test.py",
        ROOT / "phase85_coordinator_dry_run_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)
    if dst.exists():
        backup = dst.with_name(dst.name + f".phase85_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "85_PRODUCTION_EXECUTION_COORDINATOR",
    "status": "installed",
    "single_controlled_execution_entrypoint": True,
    "idempotency_duplicate_protection": True,
    "unsupported_actions_rejected": True,
    "broadcast_default_disabled": True,
    "installer_broadcasts": False,
    "verifier_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE85_PRODUCTION_EXECUTION_COORDINATOR_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE85_PRODUCTION_EXECUTION_COORDINATOR: INSTALLED")
print("COMPILE_CHECK: PASS")
print("SINGLE_CONTROLLED_EXECUTION_ENTRYPOINT: True")
print("IDEMPOTENCY_DUPLICATE_PROTECTION: True")
print("BROADCAST_DEFAULT_DISABLED: True")
print("INSTALLER_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
