PHASE 71 — ADAPTIVE SOLANA KEY LOADER

Supports Base58, Base64, JSON byte arrays, and auto-detection.
Accepts decoded 32-byte or 64-byte Solana secrets.

For common 64-byte exported Solana keys, the final 32 bytes are the public key,
so the wallet address can be checked without solders/PyNaCl.
For a 32-byte seed, this bundle does not fake public-key derivation.

INSTALL:
cd ~/storage/downloads || exit 1
unzip -o PHASE71_ADAPTIVE_SOLANA_KEY_BUNDLE.zip -d ~/companyos/phase71_adaptive_key_bundle
cd ~/companyos || exit 1
python phase71_adaptive_key_bundle/phase71_install.py

VERIFY:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase71_adaptive_key_bundle/phase71_verify.py

CHECK YOUR CONFIGURED KEY SAFELY:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase71_check_solana_key.py
