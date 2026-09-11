#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"
B=ROOT/"phase72_signer_integration_bundle"
pairs=[
(B/"solana_signer_key_adapter.py",ROOT/"companyos/walletintegration/solana_signer_key_adapter.py"),
(B/"phase72_signer_preflight.py",ROOT/"phase72_signer_preflight.py"),
]
stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups={}
for src,dst in pairs:
    txt=src.read_text(encoding="utf-8"); ast.parse(txt)
    if dst.exists():
        bak=dst.with_name(dst.name+f".phase72_backup_{stamp}")
        shutil.copy2(dst,bak); backups[str(dst)]=str(bak)
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(txt,encoding="utf-8")
    py_compile.compile(str(dst),doraise=True)

manifest={
"phase":"72_SIGNER_INTEGRATION",
"status":"installed",
"adaptive_key_loader_wired_for_signer_input":True,
"transaction_created_by_bundle":False,
"transaction_signed_by_bundle":False,
"transaction_broadcast_by_bundle":False,
"backups":backups,
}
(ROOT/"PHASE72_SIGNER_INTEGRATION_INSTALLED.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print("PHASE72_SIGNER_INTEGRATION: INSTALLED")
print("COMPILE_CHECK: PASS")
print("ADAPTIVE_KEY_INPUT: ENABLED")
print("TRANSACTION_CREATED_BY_BUNDLE: False")
print("TRANSACTION_SIGNED_BY_BUNDLE: False")
print("TRANSACTION_BROADCAST_BY_BUNDLE: False")
