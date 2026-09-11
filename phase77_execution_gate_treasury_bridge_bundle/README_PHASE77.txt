PHASE 77 — EXECUTION GATE ↔ LIVE TREASURY BRIDGE

Purpose:
- connect the execution gate decision path to the live treasury authorizer
- force a fresh balance check before financial authorization
- preserve reserve protection and stale-data rejection
- prove the bridge with a zero-value authorization test

This phase does NOT create, sign, or broadcast a transaction.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase77_execution_gate_treasury_bridge_bundle
mkdir -p phase77_execution_gate_treasury_bridge_bundle

unzip -o ~/storage/downloads/PHASE77_EXECUTION_GATE_TREASURY_BRIDGE_BUNDLE.zip \
  -d ~/companyos/phase77_execution_gate_treasury_bridge_bundle

python ~/companyos/phase77_execution_gate_treasury_bridge_bundle/phase77_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase77_execution_gate_treasury_bridge_bundle/phase77_verify.py

RUN LIVE ZERO-VALUE BRIDGE TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase77_execution_gate_bridge_test.py
