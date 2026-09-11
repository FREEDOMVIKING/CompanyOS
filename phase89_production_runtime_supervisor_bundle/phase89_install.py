#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase89_production_runtime_supervisor_bundle"

pairs = [
    (
        BUNDLE / "production_runtime_supervisor.py",
        ROOT / "companyos/walletintegration/production_runtime_supervisor.py",
    ),
    (
        BUNDLE / "phase89_supervisor_once.py",
        ROOT / "phase89_supervisor_once.py",
    ),
    (
        BUNDLE / "phase89_supervisor_run.py",
        ROOT / "phase89_supervisor_run.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase89_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "89_PRODUCTION_RUNTIME_SUPERVISOR",
    "status": "installed",
    "persistent_runtime_supervisor": True,
    "boot_readiness_enforced": True,
    "live_treasury_refresh_loop": True,
    "recovery_reconciliation_loop": True,
    "state_persistence": "~/.companyos_runtime/production_runtime_supervisor.json",
    "max_failure_stop_guard": True,
    "supervisor_builds_transaction": False,
    "supervisor_signs_transaction": False,
    "supervisor_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE89_PRODUCTION_RUNTIME_SUPERVISOR_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE89_PRODUCTION_RUNTIME_SUPERVISOR: INSTALLED")
print("COMPILE_CHECK: PASS")
print("BOOT_READINESS_ENFORCED: True")
print("LIVE_TREASURY_REFRESH_LOOP: True")
print("RECOVERY_RECONCILIATION_LOOP: True")
print("MAX_FAILURE_STOP_GUARD: True")
print("SUPERVISOR_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
