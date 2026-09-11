#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
python companyos_v22ctl health
python companyos_v22ctl recovery
echo
echo "Current CompanyOS runtime:"
bash companyosctl status || true
