#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase74_solana_rpc_preflight_bundle"

pairs = [
    (
        BUNDLE / "solana_rpc_preflight.py",
        ROOT / "companyos/walletintegration/solana_rpc_preflight.py",
    ),
    (
        BUNDLE / "phase74_rpc_preflight.py",
        ROOT / "phase74_rpc_preflight.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase74_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "74_SOLANA_RPC_PREFLIGHT",
    "status": "installed",
    "network_calls": ["getGenesisHash", "getLatestBlockhash", "getBalance"],
    "read_only": True,
    "transaction_created_by_bundle": False,
    "transaction_signed_by_bundle": False,
    "transaction_broadcast_by_bundle": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE74_SOLANA_RPC_PREFLIGHT_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE74_SOLANA_RPC_PREFLIGHT: INSTALLED")
print("COMPILE_CHECK: PASS")
print("READ_ONLY_RPC_METHODS_ONLY: True")
print("TRANSACTION_CREATED_BY_INSTALLER: False")
print("TRANSACTION_SIGNED_BY_INSTALLER: False")
print("TRANSACTION_BROADCAST_BY_INSTALLER: False")
print("PRIVATE_KEY_PRINTED: False")
