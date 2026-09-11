PHASE 83 — LIFECYCLE EXECUTION INTEGRATION

Purpose:
- connect the Phase 82 lifecycle store to the execution pipeline
- expose lifecycle hooks for:
  AUTHORIZED
  SIGNED
  SUBMITTED
  CONFIRMED
  FINALIZED
  FAILED
- keep persistent execution records synchronized with pipeline state

This bundle does NOT broadcast anything.

INSTALL:
cd ~/companyos || exit 1
rm -rf phase83_lifecycle_execution_integration_bundle
mkdir -p phase83_lifecycle_execution_integration_bundle

unzip -o ~/storage/downloads/PHASE83_LIFECYCLE_EXECUTION_INTEGRATION_BUNDLE.zip \
  -d ~/companyos/phase83_lifecycle_execution_integration_bundle

python ~/companyos/phase83_lifecycle_execution_integration_bundle/phase83_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase83_lifecycle_execution_integration_bundle/phase83_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase83_pipeline_lifecycle_test.py
