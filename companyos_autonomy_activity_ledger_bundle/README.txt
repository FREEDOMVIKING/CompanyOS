COMPANYOS AUTONOMY ACTIVITY LEDGER

Shows anti-stall autostarts, recent goals, active/completed/failed tasks, generated outputs,
runtime state, watchdog state, orchestration journal, and a conservative productive-activity signal.

Install:
cd ~/companyos
rm -rf companyos_autonomy_activity_ledger_bundle
mkdir -p companyos_autonomy_activity_ledger_bundle
unzip -o ~/storage/downloads/COMPANYOS_AUTONOMY_ACTIVITY_LEDGER_BUNDLE.zip -d ~/companyos/companyos_autonomy_activity_ledger_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_autonomy_activity_ledger_bundle/install.py
python companyos_autonomy_activity_ledger_bundle/verify.py
bash dashboard/autonomy_activity_ledger_start.sh

Open:
http://127.0.0.1:8768
