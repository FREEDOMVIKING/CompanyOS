
#!/usr/bin/env python3
import base64,json
from companyos.walletintegration.adaptive_solana_key import b58encode,decode_solana_private_key,inspect_solana_private_key
raw64=bytes(range(64)); raw32=bytes(range(32))
cases=[
("base58_64",b58encode(raw64),"auto",raw64,"base58"),
("base64_64",base64.b64encode(raw64).decode(),"auto",raw64,"base64"),
("json_64",json.dumps(list(raw64)),"auto",raw64,"json"),
("base58_32",b58encode(raw32),"base58",raw32,"base58"),
]
ok=True
for name,val,enc,exp,detexp in cases:
    raw,det=decode_solana_private_key(val,enc); passed=(raw==exp and det==detexp); ok &= passed
    print(name,"=>","PASS" if passed else "FAIL")
i64=inspect_solana_private_key(b58encode(raw64),"auto")
i32=inspect_solana_private_key(b58encode(raw32),"auto")
checks=[
("64_byte_pubkey_derivable",i64.public_key_derivable_without_crypto_backend),
("64_byte_pubkey_matches_tail",i64.public_key==b58encode(raw64[32:])),
("32_byte_not_fake_derived",i32.public_key is None),
("32_byte_valid_length",i32.valid_length),
]
for n,p in checks: ok &= p; print(n,"=>","PASS" if p else "FAIL")
print("PHASE71_ADAPTIVE_KEY_VERIFY:","PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
