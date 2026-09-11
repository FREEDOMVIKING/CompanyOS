#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "${HOME}/companyos"
python -m unittest discover -s tests_phase18301_18400 -v
