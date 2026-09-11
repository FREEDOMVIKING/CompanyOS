#!/usr/bin/env python3
from pathlib import Path
from companyos.walletintegration.solana_signer_key_adapter import load_signer_material

candidates=[
    Path.home()/".companyos_runtime"/"live_financial.env",
    Path.home()/"companyos"/".companyos_runtime"/"live_financial.env",
    Path.home()/"companyos"/"companyos_runtime"/"live_financial.env",
]
p=next((x for x in candidates if x.exists()),None)
if not p:
    raise SystemExit("PHASE72_SIGNER_PREFLIGHT: FAIL - live_financial.env not found")

cfg={}
for line in p.read_text(errors="ignore").splitlines():
    line=line.strip()
    if line and not line.startswith("#") and "=" in line:
        k,v=line.split("=",1); cfg[k.strip()]=v.strip().strip("'\"")

secret=cfg.get("SOLANA_PRIVATE_KEY","")
enc=cfg.get("SOLANA_PRIVATE_KEY_ENCODING","auto")
if not secret:
    raise SystemExit("PHASE72_SIGNER_PREFLIGHT: FAIL - SOLANA_PRIVATE_KEY missing")

m=load_signer_material(secret,enc)
print("SIGNER_KEY_NORMALIZATION: PASS")
print("DETECTED_ENCODING:",m.detected_encoding)
print("DECODED_KEY_LENGTH:",m.key_length)
print("PUBLIC_ADDRESS_AVAILABLE:",bool(m.public_address))
if m.public_address:
    print("DERIVED_SOLANA_PUBLIC_ADDRESS:",m.public_address)
print("PRIVATE_KEY_PRINTED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("TRANSACTION_BROADCAST: False")
print("PHASE72_SIGNER_PREFLIGHT: PASS")
