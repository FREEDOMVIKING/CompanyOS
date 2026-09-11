PHASE 80 — CONTROLLED SOLANA BROADCAST PIPELINE

Adds:
- gated sendTransaction wrapper
- broadcast disabled by default
- explicit confirmation token requirement
- dry-run proof that sendTransaction stays blocked
- separate MANUAL zero-lamport self-transfer broadcaster

IMPORTANT:
A zero-lamport transaction can still consume a Solana network fee.
The installer, verifier, and dry-run test NEVER broadcast.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase80_controlled_solana_broadcast_bundle
mkdir -p phase80_controlled_solana_broadcast_bundle

unzip -o ~/storage/downloads/PHASE80_CONTROLLED_SOLANA_BROADCAST_BUNDLE.zip \
  -d ~/companyos/phase80_controlled_solana_broadcast_bundle

python ~/companyos/phase80_controlled_solana_broadcast_bundle/phase80_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase80_controlled_solana_broadcast_bundle/phase80_verify.py

SAFE DRY-RUN TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase80_dry_run_test.py

DO NOT run the manual broadcast script until you deliberately choose to spend
a small network fee for an on-chain zero-lamport self-transfer test.
