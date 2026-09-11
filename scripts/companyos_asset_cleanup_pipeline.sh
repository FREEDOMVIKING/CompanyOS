#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

python scripts/companyos_asset_lifecycle_manager.py run >/dev/null
python scripts/companyos_infrastructure_cleanup.py run >/dev/null
python scripts/companyos_postlaunch_monitor.py run >/dev/null
python scripts/companyos_operations_reconciler.py reconcile >/dev/null
