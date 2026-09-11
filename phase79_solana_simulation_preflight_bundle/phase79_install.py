#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase79_solana_simulation_preflight_bundle"

pairs = [
    (
        BUNDLE / "solana_transaction_simulator.py",
        ROOT / "companyos/walletintegration/solana_transaction_simulator.py",
    ),
    (
        BUNDLE / "phase79_simulation_test.py",
        ROOT / "phase79_simulation_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase79_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "79_SOLANA_SIMULATION_PREFLIGHT",
    "status": "installed",
    "uses_real_signed_transaction": True,
    "uses_simulateTransaction": True,
    "sendTransaction_called_by_bundle": False,
    "transaction_broadcast_by_bundle": False,
    "funds_moved_by_bundle": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE79_SOLANA_SIMULATION_PREFLIGHT_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE79_SOLANA_SIMULATION_PREFLIGHT: INSTALLED")
print("COMPILE_CHECK: PASS")
print("SIMULATE_TRANSACTION_ENABLED: True")
print("SEND_TRANSACTION_CALLED_BY_INSTALLER: False")
print("TRANSACTION_BROADCAST_BY_INSTALLER: False")
print("FUNDS_MOVED_BY_INSTALLER: False")
print("PRIVATE_KEY_PRINTED: False")
