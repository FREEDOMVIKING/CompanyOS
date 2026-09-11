PHASE 74 — SOLANA RPC + WALLET READ-ONLY PREFLIGHT

Purpose:
- Confirm the configured Solana RPC is reachable.
- Confirm main Solana RPC methods respond.
- Fetch latest blockhash read-only.
- Read the configured wallet's SOL balance.
- Confirm the derived wallet address is usable with the RPC.

This phase DOES NOT:
- create a transaction
- sign a transaction
- broadcast a transaction
- print the private key

INSTALL:
cd ~/companyos || exit 1
rm -rf phase74_solana_rpc_preflight_bundle
mkdir -p phase74_solana_rpc_preflight_bundle

unzip -o ~/storage/downloads/PHASE74_SOLANA_RPC_PREFLIGHT_BUNDLE.zip \
  -d ~/companyos/phase74_solana_rpc_preflight_bundle

python ~/companyos/phase74_solana_rpc_preflight_bundle/phase74_install.py

VERIFY STACK:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase74_solana_rpc_preflight_bundle/phase74_verify.py

RUN REAL READ-ONLY RPC PREFLIGHT:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase74_rpc_preflight.py
