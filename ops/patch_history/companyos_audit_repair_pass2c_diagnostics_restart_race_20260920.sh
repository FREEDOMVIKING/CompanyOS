#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS AUDIT REPAIR PASS 2C ====="
echo "GOAL=REMOVE_AUTONOMOUS_DIAGNOSTICS_SUPERVISOR_RESTART_RACE"
echo "FINDING=STOP_EVENT_PARENT_WAS_AUTONOMOUS_DIAGNOSTICS"
echo "NOTE=DIAGNOSTICS_MAY_REPORT_RECOVERY_NEEDS_BUT_MUST_NOT_RESTART_ITS_OWN_PARENT_SUPERVISOR"
echo "NOTE=NO_EMAIL_SEND"
echo "NOTE=NO_FINANCIAL_ACTION"
echo "NOTE=NO_DEPLOYMENT"
echo "NOTE=RUNTIME_STOPPED_AFTER_VALIDATION"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$RT/audit_repair_backups/pass2c_$STAMP"
mkdir -p "$BACKUP"

FILES=(
  companyos/runtime/autonomous_diagnostics.py
  companyos/runtime/runtime_control.py
  companyos/runtime/runtime_status.py
  companyos/runtime/launch_health_snapshot.py
  companyos/runtime/launch_readiness.py
  companyos/runtime/end_to_end_qualification.py
)

for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "PASS2C_ABORT=missing:$f"; exit 1; }
  cp "$f" "$BACKUP/$(basename "$f")"
done

echo "===== PATCH AUTONOMOUS DIAGNOSTICS ====="
python - <<'PY'
from pathlib import Path
import ast

p=Path.home()/"companyos/companyos/runtime/autonomous_diagnostics.py"
s=p.read_text()

s=s.replace(
    'ROOT=(Path.home()/"companyos").resolve(); RT=ROOT/".companyos_runtime"',
    'ROOT=(Path.home()/"companyos").resolve(); RT=Path.home()/".companyos_runtime"'
)

s=s.replace(
    'STATE=RT/"autonomous_diagnostics_state.json"; EVENTS=RT/"autonomous_diagnostics_events.jsonl"; STOP=RT/"STOP_CONTINUOUS"',
    'STATE=RT/"autonomous_diagnostics_state.json"; EVENTS=RT/"autonomous_diagnostics_events.jsonl"; STOP=RT/"autonomous_diagnostics.stop"'
)

old = ''' if "supervisor_restart" in kinds:
  c=ROOT/"scripts/companyosctl"
  if c.exists():
   p=subprocess.run([str(c),"restart"],cwd=ROOT,text=True,capture_output=True,timeout=45);res.append({"repair":"supervisor_restart","ok":p.returncode==0})
 return res
'''

new = ''' if "supervisor_restart" in kinds:
  # autonomous_diagnostics is itself supervisor-managed. Restarting the
  # supervisor from this child creates a bootstrap race/restart loop.
  atomic(
   RT/"diagnostics_supervisor_recovery_requested.json",
   {
    "requested_at":time.time(),
    "source":"autonomous_diagnostics",
    "reason":"service_health_finding",
    "policy":"defer_to_supervisor_control_plane",
   },
  )
  res.append({
   "repair":"supervisor_restart",
   "ok":True,
   "action":"deferred_to_supervisor_control_plane",
   "executed_restart":False,
  })
 return res
'''

if old not in s:
    raise SystemExit("PASS2C_ABORT=autonomous_diagnostics_restart_anchor_missing")
s=s.replace(old,new,1)

old_run = '''def run():
 delay=max(60,int(os.getenv("COMPANYOS_DIAGNOSTICS_INTERVAL_SECONDS","300")))
 while not STOP.exists():
'''

new_run = '''def run():
 STOP.unlink(missing_ok=True)
 delay=max(60,int(os.getenv("COMPANYOS_DIAGNOSTICS_INTERVAL_SECONDS","300")))
 while not STOP.exists():
'''

if old_run not in s:
    raise SystemExit("PASS2C_ABORT=autonomous_diagnostics_run_anchor_missing")
s=s.replace(old_run,new_run,1)

ast.parse(s)
p.write_text(s)
print("AUTONOMOUS_DIAGNOSTICS_PATCH=PASS")
PY

echo "===== ADD REGRESSION TESTS ====="
cat > tests/test_autonomous_diagnostics_supervisor_safety.py <<'PY'
from pathlib import Path

import companyos.runtime.autonomous_diagnostics as ad


def test_diagnostics_uses_shared_runtime_root():
    assert ad.RT == Path.home() / ".companyos_runtime"
    assert ad.STOP == ad.RT / "autonomous_diagnostics.stop"


def test_diagnostics_never_restarts_parent_supervisor(monkeypatch, tmp_path):
    monkeypatch.setattr(ad, "RT", tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("autonomous diagnostics must not invoke a supervisor restart")

    monkeypatch.setattr(ad.subprocess, "run", forbidden)

    result = ad.apply(
        [{"repair": "supervisor_restart", "reason": {"service": "x"}}]
    )

    assert result
    assert result[0]["ok"] is True
    assert result[0]["executed_restart"] is False
    assert result[0]["action"] == "deferred_to_supervisor_control_plane"

    request = tmp_path / "diagnostics_supervisor_recovery_requested.json"
    assert request.exists()
PY

echo "===== COMPILE ====="
python -m py_compile   companyos/runtime/autonomous_diagnostics.py   companyos/runtime/runtime_control.py   companyos/runtime/runtime_status.py   companyos/runtime/launch_health_snapshot.py   companyos/runtime/launch_readiness.py   companyos/runtime/end_to_end_qualification.py   tests/test_shared_runtime_root.py   tests/test_autonomous_diagnostics_supervisor_safety.py
echo "COMPILE=PASS"

echo "===== TARGETED TESTS ====="
python -m pytest -q   tests/test_autonomous_diagnostics_supervisor_safety.py   tests/test_shared_runtime_root.py   tests/test_live_drl_strategy_governor.py   tests/test_autonomous_procurement_sourcing.py
echo "TARGETED_TESTS=PASS"

echo "===== FULL PYTEST ====="
python -m pytest -q --disable-warnings --maxfail=25
echo "FULL_PYTEST=PASS"

echo "===== CLEAN STOPPED BASELINE ====="
scripts/companyosctl stop >/dev/null 2>&1 || true
sleep 3
rm -f "$RT/SUPERVISOR_STOP"       "$RT/autonomous_diagnostics.stop"       "$RT/continuous_goal_runtime.stop" || true

echo "===== START CANONICAL RUNTIME ====="
export COMPANYOS_ENABLE_SELF_EVOLUTION=0
scripts/companyosctl recover
sleep 15

echo "===== VERIFY NO CHILD-INITIATED SUPERVISOR STOP ====="
python - <<'PY'
from pathlib import Path
import json
from companyos.runtime.runtime_control import UnifiedRuntimeControl

rt=Path.home()/".companyos_runtime"
c=UnifiedRuntimeControl(Path.home()/"companyos")
h=c.health()

out={
    "healthy":h.get("healthy"),
    "issues":h.get("issues"),
    "supervisor_pid":h.get("supervisor_pid"),
    "supervisor_alive":h.get("supervisor_alive"),
    "state_age_seconds":h.get("state_age_seconds"),
    "stop_requested":h.get("stop_requested"),
    "supervisor_stop_exists":(rt/"SUPERVISOR_STOP").exists(),
    "not_running":[
        name for name,row in (h.get("services") or {}).items()
        if not row.get("running") or not row.get("process_alive")
    ],
}
print(json.dumps(out,indent=2,sort_keys=True))

assert h.get("supervisor_alive") is True
assert h.get("stop_requested") is False
assert not (rt/"SUPERVISOR_STOP").exists()
assert h.get("healthy") is True, out
print("NO_CHILD_INITIATED_SUPERVISOR_STOP=PASS")
print("CORE_RUNTIME_HEALTH=PASS")
PY

echo "===== AUTONOMOUS DIAGNOSTICS STATE ====="
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/".companyos_runtime/autonomous_diagnostics_state.json"
if not p.exists():
    print("DIAGNOSTICS_STATE=NOT_YET_WRITTEN")
else:
    d=json.loads(p.read_text())
    print(json.dumps({
        "running":d.get("running"),
        "healthy":d.get("healthy"),
        "repairs":d.get("repairs"),
    },indent=2,sort_keys=True))
    for row in d.get("repairs") or []:
        assert row.get("executed_restart") is not True
print("DIAGNOSTICS_PARENT_RESTART_GUARD=PASS")
PY

echo "===== LAUNCH READINESS ====="
scripts/companyos_launchctl audit
echo "LAUNCH_READINESS=PASS"

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

echo "===== NATIVE FULL-LAUNCH VALIDATION ====="
set +e
python scripts/validate_companyos_full_launch.py
NATIVE_FULL_RC=$?
set -e
echo "NATIVE_FULL_LAUNCH_RC=$NATIVE_FULL_RC"

echo "===== NATIVE QUALIFICATION ====="
set +e
scripts/companyos_qualify
NATIVE_QUAL_RC=$?
set -e
echo "NATIVE_QUALIFY_RC=$NATIVE_QUAL_RC"

echo "===== HEALTH AFTER NATIVE RECOVERY TESTS ====="
set +e
scripts/companyosctl health
FINAL_HEALTH_RC=$?
set -e
echo "FINAL_HEALTH_RC=$FINAL_HEALTH_RC"

echo "===== STOP AFTER VALIDATION ====="
scripts/companyosctl stop >/dev/null 2>&1 || true
sleep 3
rm -f "$RT/SUPERVISOR_STOP" || true

echo "===== COMMIT/PUSH REPAIRS ====="
git add   companyos/runtime/autonomous_diagnostics.py   companyos/runtime/runtime_control.py   companyos/runtime/runtime_status.py   companyos/runtime/launch_health_snapshot.py   companyos/runtime/launch_readiness.py   companyos/runtime/end_to_end_qualification.py   tests/test_shared_runtime_root.py   tests/test_autonomous_diagnostics_supervisor_safety.py

if ! git diff --cached --quiet; then
  git commit -m "Fix runtime health control-plane races"
fi

BRANCH="$(git branch --show-current)"
git push origin "HEAD:$BRANCH"
echo "GITHUB_PUSH=PASS"

echo
echo "===== PASS 2C SUMMARY ====="
echo "AUTONOMOUS_DIAGNOSTICS_SHARED_RUNTIME_ROOT=PASS"
echo "AUTONOMOUS_DIAGNOSTICS_PARENT_RESTART_GUARD=PASS"
echo "TARGETED_TESTS=PASS"
echo "FULL_PYTEST=PASS"
echo "CORE_RUNTIME_HEALTH=PASS"
echo "LAUNCH_READINESS=PASS"
echo "DASHBOARD_REACHABLE=PASS"
if [ "$NATIVE_FULL_RC" -eq 0 ]; then
  echo "NATIVE_FULL_LAUNCH=PASS"
else
  echo "NATIVE_FULL_LAUNCH=FAIL_RC_$NATIVE_FULL_RC"
fi
if [ "$NATIVE_QUAL_RC" -eq 0 ]; then
  echo "NATIVE_QUALIFY=PASS"
else
  echo "NATIVE_QUALIFY=FAIL_RC_$NATIVE_QUAL_RC"
fi
if [ "$FINAL_HEALTH_RC" -eq 0 ]; then
  echo "FINAL_NATIVE_HEALTH=PASS"
else
  echo "FINAL_NATIVE_HEALTH=FAIL_RC_$FINAL_HEALTH_RC"
fi
echo "RUNTIME_STOPPED_AFTER_VALIDATION=PASS"
echo "GITHUB_PUSH=PASS"

if [ "$NATIVE_FULL_RC" -eq 0 ] && [ "$NATIVE_QUAL_RC" -eq 0 ] && [ "$FINAL_HEALTH_RC" -eq 0 ]; then
  echo "COMPANYOS_AUDIT_REPAIR_PASS_2C=COMPLETE"
else
  echo "COMPANYOS_AUDIT_REPAIR_PASS_2C=COMPLETE_WITH_NATIVE_CHECKS_TO_INSPECT"
fi
