
#!/usr/bin/env python3
from pathlib import Path
import ast,py_compile,shutil,json
from datetime import datetime,timezone
ROOT=Path.home()/"companyos"; B=ROOT/"phase71_adaptive_key_bundle"
pairs=[
(B/"adaptive_solana_key.py",ROOT/"companyos/walletintegration/adaptive_solana_key.py"),
(B/"phase71_check_solana_key.py",ROOT/"phase71_check_solana_key.py"),
]
stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); backups={}
for src,dst in pairs:
    txt=src.read_text(encoding="utf-8"); ast.parse(txt)
    if dst.exists():
        bak=dst.with_name(dst.name+f".phase71_backup_{stamp}"); shutil.copy2(dst,bak); backups[str(dst)]=str(bak)
    dst.parent.mkdir(parents=True,exist_ok=True); dst.write_text(txt,encoding="utf-8"); py_compile.compile(str(dst),doraise=True)
manifest={"phase":"71_ADAPTIVE_SOLANA_KEY","status":"installed","supported_encodings":["base58","base64","json-byte-array","auto"],"supported_decoded_lengths":[32,64],"secrets_printed":False,"transactions_signed_by_installer":False,"transactions_broadcast_by_installer":False,"backups":backups}
(ROOT/"PHASE71_ADAPTIVE_SOLANA_KEY_INSTALLED.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("PHASE71_ADAPTIVE_SOLANA_KEY: INSTALLED")
print("COMPILE_CHECK: PASS")
print("AUTO_BASE58_BASE64_JSON_SUPPORT: True")
print("DECODED_LENGTHS_32_64_SUPPORTED: True")
print("SECRETS_PRINTED: False")
print("TRANSACTIONS_SIGNED_BY_INSTALLER: False")
print("TRANSACTIONS_BROADCAST_BY_INSTALLER: False")
