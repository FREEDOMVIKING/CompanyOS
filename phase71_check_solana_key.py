
#!/usr/bin/env python3
from pathlib import Path
from companyos.walletintegration.adaptive_solana_key import inspect_solana_private_key

cands=[
    Path.home()/".companyos_runtime"/"live_financial.env",
    Path.home()/"companyos"/".companyos_runtime"/"live_financial.env",
    Path.home()/"companyos"/"companyos_runtime"/"live_financial.env",
]
p=next((x for x in cands if x.exists()),None)
if not p: raise SystemExit("PHASE71_CHECK: FAIL - live_financial.env not found")
cfg={}
for line in p.read_text(errors="ignore").splitlines():
    line=line.strip()
    if line and not line.startswith("#") and "=" in line:
        k,v=line.split("=",1); cfg[k.strip()]=v.strip().strip("'\"")
secret=cfg.get("SOLANA_PRIVATE_KEY","")
enc=cfg.get("SOLANA_PRIVATE_KEY_ENCODING","auto")
if not secret: raise SystemExit("PHASE71_CHECK: FAIL - SOLANA_PRIVATE_KEY missing")
info=inspect_solana_private_key(secret,enc)
print("ENV_FILE:",p)
print("DETECTED_ENCODING:",info.encoding)
print("DECODED_KEY_LENGTH:",info.key_length)
print("VALID_SOLANA_KEY_LENGTH:",info.valid_length)
print("PUBLIC_ADDRESS_DERIVABLE_WITHOUT_NATIVE_LIBS:",info.public_key_derivable_without_crypto_backend)
print("DERIVED_SOLANA_PUBLIC_ADDRESS:",info.public_key or "unavailable_for_32_byte_seed_without_crypto_backend")
print("PRIVATE_KEY_PRINTED: False")
print("TRANSACTION_SIGNED: False")
print("TRANSACTION_BROADCAST: False")
print("PHASE71_CHECK:","PASS" if info.valid_length else "FAIL")
