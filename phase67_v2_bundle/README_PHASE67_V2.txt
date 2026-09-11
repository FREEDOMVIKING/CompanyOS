PHASE 67 V2 — PENDING RECONCILIATION WORKER

Adds:
- one-shot restart-safe pending reconciliation worker
- pending transaction status command
- stale pending detection
- durable worker status JSON
- zero automatic rebroadcast behavior

Install:
cd ~/storage/downloads || exit 1
unzip -o PHASE67_V2_RECONCILIATION_WORKER_BUNDLE.zip -d ~/companyos/phase67_v2_bundle
cd ~/companyos || exit 1
python phase67_v2_bundle/phase67_v2_install.py

Verify:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase67_v2_bundle/phase67_v2_verify.py

Check current pending status:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase67_v2_pending_status.py

Run one read-only reconciliation pass:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python phase67_v2_reconcile_once.py
