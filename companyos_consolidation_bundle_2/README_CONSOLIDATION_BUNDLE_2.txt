COMPANYOS CONSOLIDATION BUNDLE 2
CEO -> Goal -> Task -> Canonical Execution Bridge

Purpose
-------
This bundle adds a non-destructive orchestration bridge above Bundle 1.

It DOES:
- accept CEO-style goals
- decompose goals into internal tasks
- persist goal/task state
- dispatch tasks through the Canonical Execution Gateway
- prevent duplicate task execution
- record orchestration journal events
- expose one-shot/status CLI commands
- preserve approval/external-action/financial boundaries

It DOES NOT:
- enable transaction broadcasting
- change wallet keys
- bypass approvals
- delete legacy runtimes
- replace the Phase 101/102 unified stack
- start permanent daemons automatically

Expected root:
  ~/companyos

Install:
  cd ~/companyos
  unzip -o ~/storage/downloads/COMPANYOS_CONSOLIDATION_BUNDLE_2.zip \
    -d ~/companyos/companyos_consolidation_bundle_2

  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_2/install.py

Verify:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_2/verify.py

Smoke test:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_consolidation_bundle_2/smoke_test.py

Status:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python scripts/companyos_orchestration_bridge.py status
