PHASE 85 — PRODUCTION EXECUTION COORDINATOR

Adds one production execution entry point above Phase 84.

Features:
- action validation
- destination validation
- amount validation
- idempotency-key duplicate protection
- lifecycle persistence through Phase 84
- broadcast remains disabled by default

Current supported live action:
zero_lamport_self_transfer

This bundle does NOT broadcast during install, verify, or dry run.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase85_production_execution_coordinator_bundle
mkdir -p phase85_production_execution_coordinator_bundle

unzip -o ~/storage/downloads/PHASE85_PRODUCTION_EXECUTION_COORDINATOR_BUNDLE.zip \
  -d ~/companyos/phase85_production_execution_coordinator_bundle

python ~/companyos/phase85_production_execution_coordinator_bundle/phase85_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase85_production_execution_coordinator_bundle/phase85_verify.py

DRY RUN + DUPLICATE PROTECTION TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase85_coordinator_dry_run_test.py
