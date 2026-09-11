PHASE 84 — LIVE EXECUTION + LIFECYCLE INTEGRATION

Adds one integrated execution engine that connects:

fresh live balance
-> treasury authorization
-> lifecycle AUTHORIZED
-> build/sign
-> SIGNED
-> controlled broadcast
-> SUBMITTED
-> signature confirmation
-> CONFIRMED
-> balance reconciliation
-> FINALIZED or FAILED

The installer/verifier never broadcast.
Broadcast remains disabled by default.

Current integrated transaction type:
zero-lamport self-transfer validation path.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase84_live_execution_lifecycle_bundle
mkdir -p phase84_live_execution_lifecycle_bundle

unzip -o ~/storage/downloads/PHASE84_LIVE_EXECUTION_LIFECYCLE_BUNDLE.zip \
  -d ~/companyos/phase84_live_execution_lifecycle_bundle

python ~/companyos/phase84_live_execution_lifecycle_bundle/phase84_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase84_live_execution_lifecycle_bundle/phase84_verify.py

DRY RUN:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase84_dry_run_test.py
