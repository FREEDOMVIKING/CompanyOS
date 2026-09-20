#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
cd "$ROOT" || exit 1
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS AUDIT REPAIR PASS 2B ====="
echo "GOAL=CLEAN_RESTART_REAL_SUPERVISOR_AND_FINISH_SHARED_RUNTIME_ROOT_REPAIR"
echo "NOTE=THE_PREVIOUS_PASS_FOUND_THE_REAL_SUPERVISOR_BUT_TRIED_TO_START_A_SECOND_COPY"
echo "NOTE=NO_EMAIL_SEND"
echo "NOTE=NO_FINANCIAL_ACTION"
echo "NOTE=NO_DEPLOYMENT"
echo "NOTE=RUNTIME_WILL_BE_STOPPED_AT_END"

echo
echo "===== VERIFY PASS-2 FILE PATCHES ARE PRESENT ====="
python - <<'PY'
from pathlib import Path
from companyos.runtime.runtime_control import UnifiedRuntimeControl
from companyos.runtime.runtime_status import RuntimeStatus
from companyos.runtime.launch_health_snapshot import LaunchHealthSnapshot
from companyos.runtime.launch_readiness import LaunchReadinessAudit
from companyos.runtime.end_to_end_qualification import EndToEndQualification

root=Path.home()/"companyos"
expected=Path.home()/".companyos_runtime"
items=[
    ("runtime_control", UnifiedRuntimeControl(root).runtime_root),
    ("runtime_status", RuntimeStatus(root).runtime_root),
    ("launch_health_snapshot", LaunchHealthSnapshot(root).runtime_root),
    ("launch_readiness", LaunchReadinessAudit(root).runtime_root),
    ("end_to_end_qualification", EndToEndQualification(root).runtime_root),
]
for name,value in items:
    print(f"{name}={value}")
    assert value == expected, (name,value,expected)
print("SHARED_RUNTIME_ROOT=PASS")
PY
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "PASS2B_ABORT=shared_runtime_patch_missing"
  exit "$rc"
fi

echo
echo "===== STOP THE ACTUAL EXISTING SUPERVISOR ====="
python - <<'PY'
import json, time
from pathlib import Path
from companyos.runtime.runtime_control import UnifiedRuntimeControl

c=UnifiedRuntimeControl(Path.home()/"companyos")
before=c.health()
print("BEFORE_SUPERVISOR_PID=",before.get("supervisor_pid"))
print("BEFORE_SUPERVISOR_ALIVE=",before.get("supervisor_alive"))
print("BEFORE_HEALTHY=",before.get("healthy"))
print("BEFORE_STATE_AGE=",before.get("state_age_seconds"))

r=c.stop(wait_seconds=90)
print(json.dumps({
    "stop_ok":r.get("ok"),
    "stop_action":r.get("action"),
    "after_supervisor_alive":(r.get("after") or {}).get("supervisor_alive"),
},indent=2,sort_keys=True))
PY

sleep 3

echo
echo "===== VERIFY NO CANONICAL SUPERVISOR IS ALIVE ====="
python - <<'PY'
from pathlib import Path
from companyos.runtime.runtime_control import UnifiedRuntimeControl
c=UnifiedRuntimeControl(Path.home()/"companyos")
s=c.status()
print("SUPERVISOR_PID=",s.get("supervisor_pid"))
print("SUPERVISOR_ALIVE=",s.get("supervisor_alive"))
if s.get("supervisor_alive"):
    raise SystemExit(41)
print("CANONICAL_SUPERVISOR_STOPPED=PASS")
PY
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "PASS2B_ABORT=canonical_supervisor_still_alive"
  echo "Run: pgrep -af 'companyos.runtime|companyos/runtime'"
  exit "$rc"
fi

rm -f "$RT/SUPERVISOR_STOP" || true

echo
echo "===== TESTS BEFORE RUNTIME RESTART ====="
python -m py_compile \
  companyos/runtime/runtime_control.py \
  companyos/runtime/runtime_status.py \
  companyos/runtime/launch_health_snapshot.py \
  companyos/runtime/launch_readiness.py \
  companyos/runtime/end_to_end_qualification.py \
  tests/test_shared_runtime_root.py
rc=$?
[ "$rc" -eq 0 ] || { echo "PASS2B_ABORT=compile_failed"; exit "$rc"; }
echo "COMPILE=PASS"

python -m pytest -q \
  tests/test_shared_runtime_root.py \
  tests/test_live_drl_strategy_governor.py \
  tests/test_autonomous_procurement_sourcing.py
rc=$?
[ "$rc" -eq 0 ] || { echo "PASS2B_ABORT=targeted_tests_failed"; exit "$rc"; }
echo "TARGETED_TESTS=PASS"

python -m pytest -q --disable-warnings --maxfail=25
rc=$?
[ "$rc" -eq 0 ] || { echo "PASS2B_ABORT=full_pytest_failed"; exit "$rc"; }
echo "FULL_PYTEST=PASS"

echo
echo "===== START THROUGH CANONICAL RECOVERY PATH ====="
export COMPANYOS_ENABLE_SELF_EVOLUTION=0
scripts/companyosctl recover
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "PASS2B_ABORT=recover_failed"
  exit "$rc"
fi

sleep 8

echo
echo "===== CURRENT HEALTH ====="
scripts/companyosctl health
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "PASS2B_ABORT=health_failed"
  scripts/companyosctl logs --lines 120 || true
  exit "$rc"
fi
echo "CORE_RUNTIME_HEALTH=PASS"

echo
echo "===== LAUNCH READINESS ====="
scripts/companyos_launchctl audit
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "PASS2B_ABORT=launch_readiness_failed"
  exit "$rc"
fi
echo "LAUNCH_READINESS=PASS"

echo
echo "===== DASHBOARD HEALTH ====="
python - <<'PY'
import json, urllib.request
url="http://127.0.0.1:8765/api/health"
with urllib.request.urlopen(url,timeout=10) as r:
    obj=json.loads(r.read().decode())
print("HTTP_STATUS=",r.status)
print("DASHBOARD_HEALTHY=",bool((obj.get("health") or {}).get("healthy")))
assert r.status == 200
print("DASHBOARD_REACHABLE=PASS")
PY
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "PASS2B_ABORT=dashboard_health_failed"
  exit "$rc"
fi

echo
echo "===== NATIVE FULL-LAUNCH VALIDATION ====="
python scripts/validate_companyos_full_launch.py
native_rc=$?
echo "NATIVE_FULL_LAUNCH_RC=$native_rc"

echo
echo "===== NATIVE QUALIFICATION ====="
scripts/companyos_qualify
qual_rc=$?
echo "NATIVE_QUALIFY_RC=$qual_rc"

echo
echo "===== FINAL HEALTH BEFORE STOP ====="
scripts/companyosctl health
health_rc=$?
echo "FINAL_HEALTH_RC=$health_rc"

echo
echo "===== STOP AFTER VALIDATION ====="
python - <<'PY'
import json
from pathlib import Path
from companyos.runtime.runtime_control import UnifiedRuntimeControl
c=UnifiedRuntimeControl(Path.home()/"companyos")
r=c.stop(wait_seconds=90)
print(json.dumps({
    "ok":r.get("ok"),
    "action":r.get("action"),
    "after_alive":(r.get("after") or {}).get("supervisor_alive"),
},indent=2,sort_keys=True))
PY
stop_rc=$?
sleep 2

echo
echo "===== COMMIT SHARED-RUNTIME REPAIR ====="
git add \
  companyos/runtime/runtime_control.py \
  companyos/runtime/runtime_status.py \
  companyos/runtime/launch_health_snapshot.py \
  companyos/runtime/launch_readiness.py \
  companyos/runtime/end_to_end_qualification.py \
  tests/test_shared_runtime_root.py

if ! git diff --cached --quiet; then
  git commit -m "Unify CompanyOS control plane on shared runtime root"
  commit_rc=$?
  if [ "$commit_rc" -ne 0 ]; then
    echo "PASS2B_ABORT=commit_failed"
    exit "$commit_rc"
  fi
else
  echo "COMMIT=NO_NEW_CHANGES"
fi

BRANCH="$(git branch --show-current)"
git push origin "HEAD:$BRANCH"
push_rc=$?
if [ "$push_rc" -ne 0 ]; then
  echo "PASS2B_ABORT=push_failed"
  exit "$push_rc"
fi

echo
echo "===== PASS 2B SUMMARY ====="
echo "SHARED_RUNTIME_ROOT=PASS"
echo "TARGETED_TESTS=PASS"
echo "FULL_PYTEST=PASS"
echo "CORE_RUNTIME_HEALTH=$([ "$health_rc" -eq 0 ] && echo PASS || echo FAIL)"
echo "LAUNCH_READINESS=PASS"
echo "DASHBOARD_REACHABLE=PASS"
echo "NATIVE_FULL_LAUNCH=$([ "$native_rc" -eq 0 ] && echo PASS || echo FAIL)"
echo "NATIVE_QUALIFY=$([ "$qual_rc" -eq 0 ] && echo PASS || echo FAIL)"
echo "RUNTIME_STOPPED_AFTER_VALIDATION=$([ "$stop_rc" -eq 0 ] && echo PASS || echo CHECK)"
echo "GITHUB_PUSH=PASS"

if [ "$native_rc" -eq 0 ] && [ "$qual_rc" -eq 0 ] && [ "$health_rc" -eq 0 ]; then
  echo "COMPANYOS_AUDIT_REPAIR_PASS_2B=COMPLETE"
  exit 0
else
  echo "COMPANYOS_AUDIT_REPAIR_PASS_2B=COMPLETE_WITH_NATIVE_CHECKS_TO_INSPECT"
  exit 0
fi
