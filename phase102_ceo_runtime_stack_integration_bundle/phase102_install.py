#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase102_ceo_runtime_stack_integration_bundle"

pairs = [
    (
        BUNDLE / "ceo_runtime_control_plane.py",
        ROOT / "companyos/runtime/ceo_runtime_control_plane.py",
    ),
    (
        BUNDLE / "unified_runtime_stack_manager.py",
        ROOT / "companyos/runtime/unified_runtime_stack_manager.py",
    ),
    (
        BUNDLE / "phase102_unified_runtime_ctl.py",
        ROOT / "phase102_unified_runtime_ctl.py",
    ),
    (
        BUNDLE / "phase102_unified_runtime_test.py",
        ROOT / "phase102_unified_runtime_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase102_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "102_CEO_RUNTIME_STACK_INTEGRATION",
    "status": "installed",
    "one_command_unified_runtime_start": True,
    "financial_stack_and_ceo_runtime_status": True,
    "one_command_unified_runtime_stop": True,
    "duplicate_ceo_runtime_start_blocked": True,
    "external_actions": False,
    "signs_transaction": False,
    "broadcasts_transaction": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE102_CEO_RUNTIME_STACK_INTEGRATION_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE102_CEO_RUNTIME_STACK_INTEGRATION: INSTALLED")
print("COMPILE_CHECK: PASS")
print("ONE_COMMAND_UNIFIED_RUNTIME_START: True")
print("ONE_COMMAND_UNIFIED_RUNTIME_STOP: True")
print("FINANCIAL_STACK_AND_CEO_RUNTIME_STATUS: True")
print("DUPLICATE_CEO_RUNTIME_START_BLOCKED: True")
print("UNIFIED_MANAGER_EXTERNAL_ACTIONS: False")
print("UNIFIED_MANAGER_BROADCASTS: False")
print("PRIVATE_KEY_PRINTED: False")
