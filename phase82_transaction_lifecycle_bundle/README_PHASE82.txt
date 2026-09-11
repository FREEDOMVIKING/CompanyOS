PHASE 82 — TRANSACTION LIFECYCLE + RECONCILIATION

Adds persistent transaction lifecycle records:

AUTHORIZED
SIGNED
SUBMITTED
CONFIRMED
FINALIZED
FAILED

Key rule:
SUBMITTED is NOT treated as success.

Each lifecycle record can store:
- wallet
- destination
- requested lamports
- signature
- confirmation status
- slot
- status error
- balance before
- balance after
- observed balance delta
- metadata

INSTALL:
cd ~/companyos || exit 1
rm -rf phase82_transaction_lifecycle_bundle
mkdir -p phase82_transaction_lifecycle_bundle

unzip -o ~/storage/downloads/PHASE82_TRANSACTION_LIFECYCLE_BUNDLE.zip \
  -d ~/companyos/phase82_transaction_lifecycle_bundle

python ~/companyos/phase82_transaction_lifecycle_bundle/phase82_install.py

VERIFY:
cd ~/companyos || exit 1
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase82_transaction_lifecycle_bundle/phase82_verify.py

TEST PERSISTENCE/STATE MACHINE:
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase82_lifecycle_test.py

RECONCILE NEWEST STORED SIGNATURE (READ-ONLY RPC):
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python phase82_reconcile_last_signature.py
