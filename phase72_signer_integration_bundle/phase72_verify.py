#!/usr/bin/env python3
import base64,json
from companyos.walletintegration.adaptive_solana_key import b58encode
from companyos.walletintegration.solana_signer_key_adapter import load_signer_material

raw64=bytes(range(64)); raw32=bytes(range(32))
cases=[
("base58_64",b58encode(raw64),"auto",64,"base58"),
("base64_64",base64.b64encode(raw64).decode(),"auto",64,"base64"),
("json_64",json.dumps(list(raw64)),"auto",64,"json"),
("base58_32",b58encode(raw32),"base58",32,"base58"),
]
ok=True
for name,val,enc,elen,eenc in cases:
    m=load_signer_material(val,enc)
    passed=(m.key_length==elen and m.detected_encoding==eenc)
    ok &= passed
    print(name,"=>","PASS" if passed else "FAIL")
print("PHASE72_SIGNER_ADAPTER_VERIFY:","PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
