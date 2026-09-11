#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

python scripts/companyos_adaptive_self_build.py run
python scripts/companyos_self_build_validator.py
