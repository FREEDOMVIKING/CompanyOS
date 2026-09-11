COMPANYOS FINAL HAUL BUNDLE
Final consolidation, launch readiness, trial-live controls, and production launch workflow.

This bundle is designed as the final consolidation pass before real-world operation.

Adds:
- final system preflight
- canonical service health validation
- stale-process / orphan cleanup
- runtime state reconciliation
- persisted launch profile
- TRIAL_LIVE profile with hard caps and explicit confirmations
- FULL_LIVE profile with explicit confirmation token and required risk limits
- launch checklist and rollback hooks
- optional Termux boot installer
- one-command status / preflight / trial / full / stop / rollback controls

Important safety defaults:
- does NOT enable live execution at install time
- does NOT change wallet keys
- does NOT bypass approval, treasury, or live-gate controls
- does NOT remove existing transaction safeguards
- full live requires explicit operator activation and configured limits

Install:
  cd ~/companyos
  unzip -o ~/storage/downloads/COMPANYOS_FINAL_HAUL_BUNDLE.zip \
    -d ~/companyos/companyos_final_haul_bundle

  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_final_haul_bundle/install.py

Verify:
  PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
  python companyos_final_haul_bundle/verify.py

Final preflight:
  bash scripts/companyos_final_launch.sh preflight

Trial-live readiness:
  bash scripts/companyos_final_launch.sh trial-check

Enable Termux boot autostart after preflight passes:
  bash scripts/companyos_final_launch.sh install-boot

Status:
  bash scripts/companyos_final_launch.sh status
