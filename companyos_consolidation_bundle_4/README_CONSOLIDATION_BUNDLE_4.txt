COMPANYOS CONSOLIDATION BUNDLE 4
Canonical Production Runtime Controller

Purpose
-------
This bundle creates one production control plane over the already-proven layers:

Phase 102 unified runtime health/supervision
-> CEO runtime bridge
-> opportunity/research bridge
-> canonical orchestration
-> canonical execution gateway
-> persistent health/audit/runtime state

It adds one master controller with:
- start
- stop
- status
- test
- once
- health

It does NOT:
- replace Phase 101/102 source
- delete legacy runtimes
- enable transaction broadcasting
- change wallet keys
- bypass approval/treasury/live gates
- auto-start at Android boot yet

Install:
  cd ~/companyos
  unzip -o ~/storage/downloads/COMPANYOS_CONSOLIDATION_BUNDLE_4.zip \
    -d ~/companyos/companyos_consolidation_bundle_4

  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_4/install.py

Verify:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_4/verify.py

Smoke:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_4/smoke_test.py

Controller:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python scripts/companyos_master_runtime.py status
