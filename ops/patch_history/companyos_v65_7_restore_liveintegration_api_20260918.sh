#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V65.7 RESTORE LIVEINTEGRATION API ====="
F="companyos/liveintegration/__init__.py"
cp "$F" "$F.v65_7_backup_$(date +%Y%m%d_%H%M%S)"
python - <<'PY'
from pathlib import Path
p=Path("companyos/liveintegration/__init__.py")
s=p.read_text()
exports=[
("ConnectorCertification","companyos.liveintegration.connector_certification"),
("RequestSanitizer","companyos.liveintegration.request_sanitizer"),
("LiveModeGate","companyos.liveintegration.live_mode_gate"),
("LivePreflight","companyos.liveintegration.preflight"),
]
added=[]
for name,mod in exports:
    needle=f"from {mod} import {name}"
    if needle not in s:
        s += f"\nfrom {mod} import {name}\n"
        added.append(name)
p.write_text(s)
print("EXPORTS_ADDED="+",".join(added))
PY
python -m py_compile companyos/liveintegration/__init__.py \
 companyos/liveintegration/connector_certification.py \
 companyos/liveintegration/request_sanitizer.py \
 companyos/liveintegration/live_mode_gate.py \
 companyos/liveintegration/preflight.py
python -m pytest -q tests/test_phase8501_9000.py --disable-warnings --maxfail=1
git diff --check
echo "V65_7_LIVEINTEGRATION_API=PASS"
echo "===== NEXT FULL-SUITE FAILURE ====="
python -m pytest -q tests --disable-warnings --maxfail=1
echo "V65_7_FULL_SUITE=PASS"
