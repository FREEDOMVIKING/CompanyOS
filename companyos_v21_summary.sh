#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
python companyos_v21ctl status
python companyos_v21ctl health
python companyos_v21ctl plan
echo
echo "Current CompanyOS runtime:"
bash companyosctl status || true
