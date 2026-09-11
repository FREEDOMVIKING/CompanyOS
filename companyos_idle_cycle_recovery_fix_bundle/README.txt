COMPANYOS IDLE-CYCLE RECOVERY FIX

Fixes the runtime state where CompanyOS is healthy but repeatedly shows:
- active_orchestrations: 0
- cycles_dispatched_this_tick: 0
- last_orchestration_id: null

Behavior:
- After 25 genuinely empty cycles, start one high-priority recovery orchestration.
- Prefer diversified opportunity discovery when available.
- Require concrete internal/reversible tasks and a persisted state change.
- Prevent duplicate/versioned Local Contractor Bid Organizer recovery work.
- Use a 5-minute cooldown to prevent recovery spam.
- Preserve external-action, financial, wallet, signer, reconciliation, and approval gates.

INSTALL

cd ~/companyos || exit 1
rm -rf companyos_idle_cycle_recovery_fix_bundle
mkdir -p companyos_idle_cycle_recovery_fix_bundle
unzip -o ~/storage/downloads/COMPANYOS_IDLE_CYCLE_RECOVERY_FIX_BUNDLE.zip -d ~/companyos/companyos_idle_cycle_recovery_fix_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_idle_cycle_recovery_fix_bundle/install.py
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_idle_cycle_recovery_fix_bundle/verify.py
bash scripts/companyos_productive_autonomy.sh restart

Check:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python scripts/companyos_idle_recovery_status.py

Watch:
http://127.0.0.1:8768

Expected recovery event:
IDLE_CYCLE_RECOVERY
