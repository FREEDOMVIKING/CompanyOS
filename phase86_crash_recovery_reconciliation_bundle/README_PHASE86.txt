PHASE 86 — CRASH RECOVERY + TRANSACTION RECONCILIATION

Purpose:
- recover persisted execution lifecycle records after Termux/app restarts
- NEVER blindly rebroadcast AUTHORIZED or SIGNED records
- for SUBMITTED records, check Solana status first
- promote to CONFIRMED / FINALIZED or mark FAILED when chain state proves it
- leave unknown/pending states untouched rather than guessing

INSTALL:
cd ~/companyos || exit 1
rm -rf phase86_crash_recovery_reconciliation_bundle
mkdir -p phase86_crash_recovery_reconciliation_bundle

unzip -o ~/storage/downloads/PHASE86_CRASH_RECOVERY_RECONCILIATION_BUNDLE.zip \
  -d ~/companyos/phase86_crash_recovery_reconciliation_bundle

python ~/companyos/phase86_crash_recovery_reconciliation_bundle/phase86_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase86_crash_recovery_reconciliation_bundle/phase86_verify.py

TEST:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase86_recovery_test.py

RUNTIME RECOVERY / READ-ONLY ONCHAIN RECONCILIATION:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase86_recover_runtime.py
