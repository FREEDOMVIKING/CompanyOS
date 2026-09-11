PHASE 66 V2 — PERSISTENT PENDING TRANSACTION RECOVERY

Adds restart-safe pending transaction tracking and read-only confirmation reconciliation.

Safety:
- no automatic rebroadcasts
- no signing in recovery code
- no transaction creation in recovery code
- confirmation checks are read-only RPC calls
- timestamped backups are created before modifying existing files

Install:
cd ~/companyos || exit 1
python phase66_v2_install_pending_recovery.py

Verify:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase66_v2_verify.py

Manual read-only reconciliation:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase66_v2_reconcile_pending.py
