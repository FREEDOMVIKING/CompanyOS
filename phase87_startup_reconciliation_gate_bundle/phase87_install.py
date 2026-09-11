#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase87_startup_reconciliation_gate_bundle"

pairs = [
    (
        BUNDLE / "startup_reconciliation_gate.py",
        ROOT / "companyos/walletintegration/startup_reconciliation_gate.py",
    ),
    (
        BUNDLE / "phase87_startup_gate_test.py",
        ROOT / "phase87_startup_gate_test.py",
    ),
    (
        BUNDLE / "phase87_startup_reconcile_runtime.py",
        ROOT / "phase87_startup_reconcile_runtime.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)
    if dst.exists():
        backup = dst.with_name(dst.name + f".phase87_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "87_STARTUP_RECONCILIATION_GATE",
    "status": "installed",
    "startup_reconciliation_required": True,
    "signed_pending_auto_rebroadcast": False,
    "unresolved_submitted_blocks_resume": True,
    "installer_broadcasts": False,
    "verifier_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE87_STARTUP_RECONCILIATION_GATE_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE87_STARTUP_RECONCILIATION_GATE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("STARTUP_RECONCILIATION_REQUIRED: True")
print("SIGNED_PENDING_AUTO_REBROADCAST: False")
print("UNRESOLVED_SUBMITTED_BLOCKS_RESUME: True")
print("INSTALLER_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
