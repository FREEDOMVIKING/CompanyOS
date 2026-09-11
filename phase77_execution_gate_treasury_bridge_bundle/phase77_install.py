#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase77_execution_gate_treasury_bridge_bundle"

pairs = [
    (
        BUNDLE / "execution_gate_treasury_bridge.py",
        ROOT / "companyos/walletintegration/execution_gate_treasury_bridge.py",
    ),
    (
        BUNDLE / "phase77_execution_gate_bridge_test.py",
        ROOT / "phase77_execution_gate_bridge_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase77_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "77_EXECUTION_GATE_TREASURY_BRIDGE",
    "status": "installed",
    "execution_gate_fresh_treasury_bridge": True,
    "zero_value_test_only": True,
    "transaction_created_by_bundle": False,
    "transaction_signed_by_bundle": False,
    "transaction_broadcast_by_bundle": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE77_EXECUTION_GATE_TREASURY_BRIDGE_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE77_EXECUTION_GATE_TREASURY_BRIDGE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("EXECUTION_GATE_FRESH_TREASURY_BRIDGE: True")
print("ZERO_VALUE_TEST_ONLY: True")
print("TRANSACTION_CREATED_BY_INSTALLER: False")
print("TRANSACTION_SIGNED_BY_INSTALLER: False")
print("TRANSACTION_BROADCAST_BY_INSTALLER: False")
print("PRIVATE_KEY_PRINTED: False")
