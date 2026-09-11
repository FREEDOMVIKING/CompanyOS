COMPANYOS LIVE AUTONOMY ACTIVITY LEDGER FIX

Fixes the stale Activity Ledger on port 8768.

What it does:
- Reads current full-autonomy journal(s)
- Reads current CEO orchestration journal(s)
- Reads productive-autonomy watchdog logs/state
- Reads current runtime state files
- Reads lifecycle/progression state
- Reads newly generated artifacts
- De-duplicates events
- Sorts activity chronologically
- Refreshes every 5 seconds
- Sends no-cache headers so the browser does not show a stale page
- Shows source file health/timestamps so stale data is obvious

It does NOT modify bot autonomy logic, wallet configuration, financial limits, or approval gates.

INSTALL

cd ~/companyos || exit 1

rm -rf companyos_live_activity_ledger_fix_bundle
mkdir -p companyos_live_activity_ledger_fix_bundle

unzip -o ~/storage/downloads/COMPANYOS_LIVE_ACTIVITY_LEDGER_FIX_BUNDLE.zip \
  -d ~/companyos/companyos_live_activity_ledger_fix_bundle

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python companyos_live_activity_ledger_fix_bundle/install.py

PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" \
python companyos_live_activity_ledger_fix_bundle/verify.py

bash dashboard/autonomy_activity_ledger_start.sh

Open:
http://127.0.0.1:8768
