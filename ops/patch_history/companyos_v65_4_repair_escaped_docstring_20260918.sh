#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V65.4 REPAIR ESCAPED DOCSTRING ====="
F="companyos_phase285_292/persistent_improver.py"
cp "$F" "$F.v65_4_backup_$(date +%Y%m%d_%H%M%S)"
python - <<'PY'
from pathlib import Path
p=Path("companyos_phase285_292/persistent_improver.py")
s=p.read_text()
old=r'    \"\"\"Persistent improvement with exactly one autonomous cycle per requested round.\"\"\"'
new='    """Persistent improvement with exactly one autonomous cycle per requested round."""'
if old not in s:
    raise SystemExit("V65_4_ABORT=escaped docstring pattern not found")
p.write_text(s.replace(old,new,1))
print("ESCAPED_DOCSTRING_REPAIRED=1")
PY
python -m py_compile "$F"
python -m pytest -q tests/test_phase285_292.py --disable-warnings --maxfail=1
git diff --check
echo "V65_4_PHASE285_REPAIR=PASS"
echo "===== NEXT FULL-SUITE FAILURE ====="
python -m pytest -q tests --disable-warnings --maxfail=1
echo "V65_4_FULL_SUITE=PASS"
