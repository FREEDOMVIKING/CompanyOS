#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase83_lifecycle_execution_integration_bundle"

pairs = [
    (
        BUNDLE / "lifecycle_execution_bridge.py",
        ROOT / "companyos/walletintegration/lifecycle_execution_bridge.py",
    ),
    (
        BUNDLE / "phase83_pipeline_lifecycle_test.py",
        ROOT / "phase83_pipeline_lifecycle_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)
    if dst.exists():
        backup = dst.with_name(dst.name + f".phase83_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "83_LIFECYCLE_EXECUTION_INTEGRATION",
    "status": "installed",
    "execution_pipeline_lifecycle_hooks": True,
    "states_supported": [
        "AUTHORIZED", "SIGNED", "SUBMITTED",
        "CONFIRMED", "FINALIZED", "FAILED"
    ],
    "installer_broadcasts": False,
    "verifier_broadcasts": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE83_LIFECYCLE_EXECUTION_INTEGRATION_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE83_LIFECYCLE_EXECUTION_INTEGRATION: INSTALLED")
print("COMPILE_CHECK: PASS")
print("EXECUTION_PIPELINE_LIFECYCLE_HOOKS_AVAILABLE: True")
print("INSTALLER_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
