CompanyOS Ledger Timestamp + Dedupe Fix

Installs the corrected port 8768 Activity Ledger.

Install:
cd ~/companyos || exit 1
rm -rf companyos_ledger_timestamp_dedupe_fix_bundle
mkdir -p companyos_ledger_timestamp_dedupe_fix_bundle
unzip -o ~/storage/downloads/COMPANYOS_LEDGER_TIMESTAMP_DEDUPE_FIX_BUNDLE.zip -d ~/companyos/companyos_ledger_timestamp_dedupe_fix_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_ledger_timestamp_dedupe_fix_bundle/install.py
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_ledger_timestamp_dedupe_fix_bundle/verify.py
bash dashboard/autonomy_activity_ledger_start.sh

Open http://127.0.0.1:8768
