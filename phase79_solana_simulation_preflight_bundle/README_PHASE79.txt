PHASE 79 — SOLANA SIMULATION PREFLIGHT

Purpose:
- build the real signed zero-lamport self-transfer from Phase 78
- call Solana simulateTransaction with signature verification enabled
- verify the cluster accepts the serialized signed transaction structurally
- inspect simulation result/logs
- keep sendTransaction disabled in this test

This phase DOES NOT broadcast and DOES NOT move funds.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase79_solana_simulation_preflight_bundle
mkdir -p phase79_solana_simulation_preflight_bundle

unzip -o ~/storage/downloads/PHASE79_SOLANA_SIMULATION_PREFLIGHT_BUNDLE.zip \
  -d ~/companyos/phase79_solana_simulation_preflight_bundle

python ~/companyos/phase79_solana_simulation_preflight_bundle/phase79_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase79_solana_simulation_preflight_bundle/phase79_verify.py

RUN REAL SIGNED TRANSACTION SIMULATION:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase79_simulation_test.py
