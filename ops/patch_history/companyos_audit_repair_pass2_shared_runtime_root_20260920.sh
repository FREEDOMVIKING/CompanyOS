#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS AUDIT REPAIR PASS 2 ====="
echo "GOAL=RECONCILE_RUNTIME_CONTROL_WITH_SHARED_RUNTIME_ROOT"
echo "NOTE=FIXES_STALE_SPLIT_STATE_BETWEEN ~/companyos/.companyos_runtime AND ~/.companyos_runtime"
echo "NOTE=NO_EMAIL_SEND"
echo "NOTE=NO_FINANCIAL_ACTION"
echo "NOTE=NO_DEPLOYMENT"
echo "NOTE=RUNTIME_IS_STOPPED_AGAIN_AFTER_VALIDATION"

STAMP="$(date +%Y%m%d_%H%M%S)"
B="$HOME/.companyos_runtime/audit_repair_backups/pass2_$STAMP"
mkdir -p "$B"

FILES=(
  companyos/runtime/runtime_control.py
  companyos/runtime/runtime_status.py
  companyos/runtime/launch_health_snapshot.py
  companyos/runtime/launch_readiness.py
  companyos/runtime/end_to_end_qualification.py
)

for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "ABORT=missing:$f"; exit 1; }
  cp "$f" "$B/$(basename "$f")"
done

echo "===== PATCH SHARED RUNTIME ROOT ====="
python - <<'PY'
from pathlib import Path
import ast

root=Path.home()/"companyos"
targets=[
    root/"companyos/runtime/runtime_control.py",
    root/"companyos/runtime/runtime_status.py",
    root/"companyos/runtime/launch_health_snapshot.py",
    root/"companyos/runtime/launch_readiness.py",
    root/"companyos/runtime/end_to_end_qualification.py",
]

changed=[]
for p in targets:
    s=p.read_text()
    old='self.runtime_root = self.root / ".companyos_runtime"'
    new='self.runtime_root = Path.home() / ".companyos_runtime"'
    if old in s:
        s=s.replace(old,new)
        changed.append(str(p.relative_to(root)))
    elif 'self.runtime_root = Path.home() / ".companyos_runtime"' not in s:
        raise SystemExit(f"ABORT=runtime_root_anchor_missing:{p}")
    ast.parse(s)
    p.write_text(s)

print("PATCHED_FILES=",len(changed))
for x in changed:
    print("PATCHED=",x)
PY

echo "===== ADD REGRESSION TEST ====="
cat > tests/test_shared_runtime_root.py <<'PY'
from pathlib import Path

from companyos.runtime.runtime_control import UnifiedRuntimeControl
from companyos.runtime.runtime_status import RuntimeStatus
from companyos.runtime.launch_health_snapshot import LaunchHealthSnapshot
from companyos.runtime.launch_readiness import LaunchReadinessAudit
from companyos.runtime.end_to_end_qualification import EndToEndQualification


def test_control_plane_uses_shared_home_runtime_root():
    expected = Path.home() / ".companyos_runtime"
    root = Path.home() / "companyos"

    assert UnifiedRuntimeControl(root).runtime_root == expected
    assert RuntimeStatus(root).runtime_root == expected
    assert LaunchHealthSnapshot(root).runtime_root == expected
    assert LaunchReadinessAudit(root).runtime_root == expected
    assert EndToEndQualification(root).runtime_root == expected
PY

echo "===== COMPILE ====="
python -m py_compile "${FILES[@]}" tests/test_shared_runtime_root.py
echo "COMPILE=PASS"

echo "===== TARGETED TESTS ====="
python -m pytest -q   tests/test_shared_runtime_root.py   tests/test_live_drl_strategy_governor.py   tests/test_autonomous_procurement_sourcing.py
echo "TARGETED_TESTS=PASS"

echo "===== FULL PYTEST ====="
python -m pytest -q --disable-warnings --maxfail=25
echo "FULL_PYTEST=PASS"

echo "===== CONTROLLED CORE RUNTIME VALIDATION ====="
# Ensure no stale supervisor stop marker blocks the fresh test.
rm -f "$HOME/.companyos_runtime/SUPERVISOR_STOP" || true

# Keep self-evolution disabled for this validation run; we are checking runtime
# control/health, not asking the bot to modify itself.
export COMPANYOS_ENABLE_SELF_EVOLUTION=0

# Start through the canonical control plane.
scripts/companyosctl start
sleep 6

echo "===== HEALTH AFTER START ====="
scripts/companyosctl health

echo "===== LAUNCH READINESS ====="
scripts/companyos_launchctl audit

echo "===== STATUS SNAPSHOT ====="
scripts/companyos_launchctl status

echo "===== STOP AFTER VALIDATION ====="
scripts/companyosctl stop || true
sleep 2

echo "===== FINAL STOPPED STATUS ====="
scripts/companyosctl status || true

echo "===== GIT COMMIT/PUSH ====="
git add "${FILES[@]}" tests/test_shared_runtime_root.py
if ! git diff --cached --quiet; then
  git commit -m "Unify CompanyOS control plane on shared runtime root"
fi
BRANCH="$(git branch --show-current)"
git push origin "HEAD:$BRANCH"
echo "GITHUB_PUSH=PASS"

echo "COMPANYOS_AUDIT_REPAIR_PASS_2=COMPLETE"
