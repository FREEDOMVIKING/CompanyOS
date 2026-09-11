COMPANYOS CONSOLIDATION BUNDLE 3
Unified CEO Runtime -> Opportunity/Research -> Canonical Orchestration Spine

Purpose
-------
This bundle connects the already-proven Phase 101/102 unified CEO runtime to the
canonical orchestration/execution layers from Bundles 1 and 2.

It adds:
- runtime cycle observer
- opportunity intake bridge
- research-to-goal conversion
- CEO goal submission adapter
- persistent runtime handoff journal
- non-destructive health/status CLI
- one-shot integration test
- startup-safe bridge hooks

It does NOT:
- replace Phase 101/102
- start permanent daemons automatically
- enable transaction broadcasting
- bypass approval/treasury/live gates
- modify wallet keys
- delete old phase code

Install:
  cd ~/companyos
  unzip -o ~/storage/downloads/COMPANYOS_CONSOLIDATION_BUNDLE_3.zip \
    -d ~/companyos/companyos_consolidation_bundle_3

  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_3/install.py

Verify:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_3/verify.py

Smoke:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_3/smoke_test.py
