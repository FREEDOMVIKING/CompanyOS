COMPANYOS MASTER CONTROL DASHBOARD BUNDLE

Adds a Master Control Center to the existing dashboard setup.

Controls:
- Autonomous CEO start/stop/restart/status
- SAFE / TRIAL_LIVE / FULL_LIVE
- Max single / max daily / max failures
- Confirmation token entry
- Preflight / full-check
- Gateway state
- Logs
- Dashboard server status

Install:
cd ~/companyos
rm -rf companyos_master_control_dashboard_bundle
mkdir -p companyos_master_control_dashboard_bundle
unzip -o ~/storage/downloads/COMPANYOS_MASTER_CONTROL_DASHBOARD_BUNDLE.zip -d ~/companyos/companyos_master_control_dashboard_bundle
PYTHONPATH="$HOME/companyos:$HOME/companyos/companyos" python companyos_master_control_dashboard_bundle/install.py
python companyos_master_control_dashboard_bundle/verify.py
bash dashboard/master_control_start.sh

Open:
http://127.0.0.1:8766

Existing Executive Dashboard:
http://127.0.0.1:8765
