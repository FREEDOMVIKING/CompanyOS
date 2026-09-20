#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V65.1 CONTROLPLANE EXPORT FIX ====="
F=companyos/controlplane/__init__.py
cp "$F" "$F.v65_1_backup_$(date +%Y%m%d_%H%M%S)"
python - <<'PY'
from pathlib import Path
p=Path("companyos/controlplane/__init__.py")
s=p.read_text()
imports=[
"from .deadlock_detector import DeadlockDetector",
"from .budget_governor import BudgetGovernor",
"from .runtime_guardrails import RuntimeGuardrails",
]
for x in imports:
    if x not in s: s += x+"\n"
# Keep __all__ accurate without disturbing ControlPlane.
s=s.replace("__all__ = ['ControlPlane']", "__all__ = ['ControlPlane', 'DeadlockDetector', 'BudgetGovernor', 'RuntimeGuardrails']")
p.write_text(s)
print("CONTROLPLANE_EXPORT_PATCH=APPLIED")
PY
python - <<'PY'
from companyos.controlplane import DeadlockDetector, BudgetGovernor, RuntimeGuardrails
print("CONTROLPLANE_IMPORTS=PASS")
PY
python -m pytest -q tests/test_phase2601_3000.py --disable-warnings --maxfail=1
git diff --check
echo "V65_1_CONTROLPLANE_EXPORT_FIX=PASS"
echo "===== NEXT FULL-SUITE FAILURE ====="
python -m pytest -q tests --disable-warnings --maxfail=1
echo "V65_1_FULL_SUITE=PASS"
