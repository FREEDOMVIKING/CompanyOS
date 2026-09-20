#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V65.3 RESTORE PERSISTENT IMPROVER ====="
F="companyos_phase285_292/persistent_improver.py"
cp "$F" "$F.v65_3_backup_$(date +%Y%m%d_%H%M%S)"
git show origin/companyos-continuous-fix-2026-09-11:"$F" > "$F"
python -m py_compile "$F" tests/test_phase285_292.py
python -m pytest -q tests/test_phase285_292.py --disable-warnings --maxfail=1
git diff --check
echo "V65_3_PERSISTENT_IMPROVER_RESTORE=PASS"
echo "===== NEXT FULL-SUITE FAILURE ====="
python -m pytest -q tests --disable-warnings --maxfail=1
echo "V65_3_FULL_SUITE=PASS"
