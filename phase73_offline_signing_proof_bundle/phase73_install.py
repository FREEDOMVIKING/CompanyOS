#!/usr/bin/env python3
from pathlib import Path
import ast
import json
import py_compile
import shutil
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
BUNDLE = ROOT / "phase73_offline_signing_proof_bundle"

pairs = [
    (
        BUNDLE / "offline_ed25519_proof.py",
        ROOT / "companyos/walletintegration/offline_ed25519_proof.py",
    ),
    (
        BUNDLE / "phase73_offline_signing_test.py",
        ROOT / "phase73_offline_signing_test.py",
    ),
]

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups = {}

for src, dst in pairs:
    text = src.read_text(encoding="utf-8")
    ast.parse(text)

    if dst.exists():
        backup = dst.with_name(dst.name + f".phase73_backup_{stamp}")
        shutil.copy2(dst, backup)
        backups[str(dst)] = str(backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)

manifest = {
    "phase": "73_OFFLINE_ED25519_SIGNING_PROOF",
    "status": "installed",
    "uses_existing_phase71_phase72_key_pipeline": True,
    "offline_signature_only": True,
    "rpc_called_by_bundle": False,
    "transaction_created_by_bundle": False,
    "transaction_broadcast_by_bundle": False,
    "private_key_printed": False,
    "backups": backups,
}

(ROOT / "PHASE73_OFFLINE_SIGNING_PROOF_INSTALLED.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)

print("PHASE73_OFFLINE_ED25519_SIGNING_PROOF: INSTALLED")
print("COMPILE_CHECK: PASS")
print("USES_PHASE71_PHASE72_PIPELINE: True")
print("RPC_CALLED_BY_INSTALLER: False")
print("TRANSACTION_CREATED_BY_INSTALLER: False")
print("TRANSACTION_BROADCAST_BY_INSTALLER: False")
print("PRIVATE_KEY_PRINTED: False")
