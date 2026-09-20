#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V64.1 FIX ADAPTIVE WORKER STATE ====="
F="companyos/runtime/adaptive_worker_factory.py"
cp "$F" "$F.v64_1_backup_$(date +%Y%m%d_%H%M%S)"
python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/adaptive_worker_factory.py")
s=p.read_text()
old='ROOT=(Path.home()/"companyos").resolve(); RT=Path.home()/".companyos_runtime" # V32_CANONICAL_RUNTIME_ROOT; STATE=RT/"adaptive_workers"\nSTATE.mkdir(parents=True,exist_ok=True)'
new='ROOT=(Path.home()/"companyos").resolve()\nRT=Path.home()/".companyos_runtime"  # V32_CANONICAL_RUNTIME_ROOT\nSTATE=RT/"adaptive_workers"\nSTATE.mkdir(parents=True,exist_ok=True)'
if old not in s: raise SystemExit("V64_1_ABORT=expected malformed STATE line not found")
p.write_text(s.replace(old,new,1))
print("PATCH_APPLIED=1")
PY
python -m py_compile "$F"
python -m pytest -q tests/generated/test_adaptive_worker_factory.py --disable-warnings --maxfail=1
echo "===== DIFF ====="
git diff --check
git diff -- "$F" | sed -n '1,120p'
echo "V64_1_ADAPTIVE_WORKER_FIX=PASS"
