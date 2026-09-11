PHASE 73 — OFFLINE ED25519 SIGNING PROOF

Purpose:
- Use the validated Phase 71 + Phase 72 adaptive Solana key pipeline.
- Create a harmless OFFLINE Ed25519 signature over a fixed challenge.
- Verify that signature locally with OpenSSL.
- Prove that the configured 64-byte Solana/Phantom key can actually sign.

Safety properties:
- No Solana transaction is created.
- No RPC request is made.
- Nothing is broadcast.
- The private key is never printed.
- Temporary private-key DER is written mode 0600 and deleted automatically.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase73_offline_signing_proof_bundle
mkdir -p phase73_offline_signing_proof_bundle

unzip -o ~/storage/downloads/PHASE73_OFFLINE_ED25519_SIGNING_PROOF_BUNDLE.zip \
  -d ~/companyos/phase73_offline_signing_proof_bundle

python ~/companyos/phase73_offline_signing_proof_bundle/phase73_install.py

VERIFY INSTALLATION:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase73_offline_signing_proof_bundle/phase73_verify.py

RUN OFFLINE SIGNING PROOF:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase73_offline_signing_test.py
