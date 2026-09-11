#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/companyos"
python scripts/companyos_redeployment_engine.py run >/dev/null
python scripts/companyos_replacement_reconciler.py reconcile >/dev/null
python scripts/companyos_postlaunch_monitor.py run >/dev/null
python scripts/companyos_operations_reconciler.py reconcile >/dev/null
