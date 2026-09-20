#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V65.6 CONNECTOR CERTIFICATION FORENSICS ====="
echo "--- package init ---"
sed -n '1,240p' companyos/liveintegration/__init__.py || true
echo "--- exact symbol search ---"
grep -RIn --exclude-dir=.git --exclude='*.pyc' \
  -E 'class[[:space:]]+ConnectorCertification|ConnectorCertification[[:space:]]*=|def[[:space:]]+ConnectorCertification' \
  companyos tests 2>/dev/null | head -80 || true
echo "--- related certification symbols ---"
grep -RIn --exclude-dir=.git --exclude='*.pyc' \
  -E 'Certification|RequestSanitizer|LiveModeGate|LivePreflight' \
  companyos/liveintegration tests/test_phase8501_9000.py 2>/dev/null | head -160 || true
echo "--- test contract ---"
sed -n '1,260p' tests/test_phase8501_9000.py
echo "--- git history candidates ---"
git log --all --oneline -- companyos/liveintegration tests/test_phase8501_9000.py | head -40 || true
echo "DATABASE_WRITES=0"
echo "SOURCE_WRITES=0"
echo "V65_6_FORENSICS=PASS"
