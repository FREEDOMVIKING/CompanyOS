#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V64.7 EXPORT CAPABILITY API + PUSH ====="
F="companyos/capabilityops/__init__.py"
cp "$F" "$F.v64_7_backup_$(date +%Y%m%d_%H%M%S)"
python - <<'PY'
from pathlib import Path
p=Path("companyos/capabilityops/__init__.py")
s=p.read_text()
adds=[
"from .capability_policy import CapabilityPolicy",
"from .capability_registry import CapabilityRegistry",
"from .real_execution_bridge import RealExecutionBridge",
]
for line in adds:
    if line not in s: s += line+"\n"
p.write_text(s)
print("EXPORT_PATCH_APPLIED=1")
PY
python -m pytest -q tests/test_phase16001_16500.py --disable-warnings --maxfail=1
git diff --check
echo "===== STAGING VERIFIED REPAIRS ====="
git add -- companyos/runtime/autonomous_task_queue.py companyos/runtime/adaptive_worker_factory.py tests/generated/test_adaptive_workforce_execution_bridge.py companyos/resilienceops/data_integrity.py companyos/capabilityops/__init__.py
git diff --cached --check
git diff --cached --stat
git commit -m "fix: reconcile runtime queue and compatibility interfaces"
git push origin companyos-continuous-fix-2026-09-11
echo "COMMIT=$(git rev-parse HEAD)"
echo "V64_7_CAPABILITY_FIX_AND_PUSH=PASS"
