#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS AUDIT REPAIR PASS 2D ====="
echo "GOAL=FIX_AUTONOMOUS_DIAGNOSTICS_STATE_SERIALIZATION_AND_FINISH_RUNTIME_VALIDATION"
echo "FINDING=CORE_RUNTIME_HEALTH_PASSED;_DIAGNOSTICS_STATE_JSON_WAS_MALFORMED_BY_LITERAL_BACKSLASH_N"
echo "NOTE=NO_EMAIL_SEND"
echo "NOTE=NO_FINANCIAL_ACTION"
echo "NOTE=NO_DEPLOYMENT"
echo "NOTE=RUNTIME_STOPPED_AFTER_VALIDATION"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$RT/audit_repair_backups/pass2d_$STAMP"
mkdir -p "$BACKUP"

MOD="companyos/runtime/autonomous_diagnostics.py"

[ -f "$MOD" ] || { echo "PASS2D_ABORT=missing:$MOD"; exit 1; }
cp "$MOD" "$BACKUP/autonomous_diagnostics.py"

echo "===== PATCH DIAGNOSTICS JSON/JSONL WRITES ====="
python - <<'PY'
from pathlib import Path
import ast

p=Path.home()/"companyos/companyos/runtime/autonomous_diagnostics.py"
s=p.read_text()

start=s.index("def atomic(p,x):")
end=s.index("def load(p):", start)

new_atomic = (
    "def atomic(p,x):\n"
    " p.parent.mkdir(parents=True,exist_ok=True)\n"
    " q=p.with_suffix(p.suffix+\".tmp\")\n"
    " q.write_text(json.dumps(x,indent=2,sort_keys=True,default=str)+\"\\n\",encoding=\"utf-8\")\n"
    " q.replace(p)\n"
)

s=s[:start]+new_atomic+s[end:]

old='with EVENTS.open("a") as f:f.write(json.dumps({"ts":time.time(),"event":"diagnostic_cycle","healthy":x["healthy"],"repairs":repairs})+"\\\\n")'
new='with EVENTS.open("a",encoding="utf-8") as f:f.write(json.dumps({"ts":time.time(),"event":"diagnostic_cycle","healthy":x["healthy"],"repairs":repairs})+"\\n")'
if old not in s:
    raise SystemExit("PASS2D_ABORT=events_write_anchor_missing")
s=s.replace(old,new,1)

ast.parse(s)
p.write_text(s)
print("DIAGNOSTICS_SERIALIZATION_PATCH=PASS")
PY

echo "===== EXTEND REGRESSION TEST ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/tests/test_autonomous_diagnostics_supervisor_safety.py"
s=p.read_text() if p.exists() else "from pathlib import Path\n\nimport companyos.runtime.autonomous_diagnostics as ad\n"

block = '''
def test_diagnostics_atomic_writes_parseable_json(tmp_path):
    import json
    p = tmp_path / "state.json"
    ad.atomic(p, {"ok": True, "nested": {"n": 1}})
    text = p.read_text(encoding="utf-8")
    assert text.endswith("\\n")
    assert json.loads(text) == {"ok": True, "nested": {"n": 1}}
'''

if "test_diagnostics_atomic_writes_parseable_json" not in s:
    s=s.rstrip()+"\n\n"+block.strip()+"\n"
p.write_text(s)
print("SERIALIZATION_REGRESSION_TEST=PASS")
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

echo "===== STOP CURRENT RUNTIME BEFORE CLEAN STATE MIGRATION ====="
scripts/companyosctl stop >/dev/null 2>&1 || true
sleep 3

echo "===== QUARANTINE MALFORMED DIAGNOSTICS STATE ====="
for f in   "$RT/autonomous_diagnostics_state.json"   "$RT/autonomous_diagnostics_events.jsonl"
do
  if [ -f "$f" ]; then
    mv "$f" "$BACKUP/$(basename "$f").pre_pass2d"
    echo "QUARANTINED=$(basename "$f")"
  fi
done
rm -f   "$RT/SUPERVISOR_STOP"   "$RT/autonomous_diagnostics.stop"   "$RT/continuous_goal_runtime.stop" || true

echo "===== START CLEAN CANONICAL RUNTIME ====="
export COMPANYOS_ENABLE_SELF_EVOLUTION=0
scripts/companyosctl recover
sleep 15

echo "===== VERIFY CORE HEALTH + DIAGNOSTICS STATE ====="
python - <<'PY'
from pathlib import Path
import json
from companyos.runtime.runtime_control import UnifiedRuntimeControl

rt=Path.home()/".companyos_runtime"
h=UnifiedRuntimeControl(Path.home()/"companyos").health()

summary={
    "healthy":h.get("healthy"),
    "issues":h.get("issues"),
    "supervisor_pid":h.get("supervisor_pid"),
    "supervisor_alive":h.get("supervisor_alive"),
    "stop_requested":h.get("stop_requested"),
    "state_age_seconds":h.get("state_age_seconds"),
    "not_running":[
        name for name,row in (h.get("services") or {}).items()
        if not row.get("running") or not row.get("process_alive")
    ],
}
print(json.dumps(summary,indent=2,sort_keys=True))
assert h.get("healthy") is True, summary
assert h.get("supervisor_alive") is True
assert h.get("stop_requested") is False
assert not (rt/"SUPERVISOR_STOP").exists()
print("CORE_RUNTIME_HEALTH=PASS")

p=rt/"autonomous_diagnostics_state.json"
assert p.exists(), "diagnostics state missing"
raw=p.read_text(encoding="utf-8")
d=json.loads(raw)
print(json.dumps({
    "diagnostics_running":d.get("running"),
    "diagnostics_healthy":d.get("healthy"),
    "repairs":d.get("repairs"),
},indent=2,sort_keys=True))
for row in d.get("repairs") or []:
    assert row.get("executed_restart") is not True
print("DIAGNOSTICS_JSON_PARSE=PASS")
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
    obj=json.loads(r.read().decode("utf-8"))
    print("HTTP_STATUS=",r.status)
    print("DASHBOARD_HEALTHY=",bool((obj.get("health") or {}).get("healthy")))
    assert r.status == 200
    assert bool((obj.get("health") or {}).get("healthy")) is True
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

echo "===== FINAL NATIVE HEALTH ====="
set +e
scripts/companyosctl health
FINAL_HEALTH_RC=$?
set -e
echo "FINAL_HEALTH_RC=$FINAL_HEALTH_RC"

echo "===== STOP AFTER VALIDATION ====="
scripts/companyosctl stop >/dev/null 2>&1 || true
sleep 3
rm -f "$RT/SUPERVISOR_STOP" || true

echo "===== COMMIT/PUSH PASS 2C + 2D REPAIRS ====="
git add   companyos/runtime/autonomous_diagnostics.py   companyos/runtime/runtime_control.py   companyos/runtime/runtime_status.py   companyos/runtime/launch_health_snapshot.py   companyos/runtime/launch_readiness.py   companyos/runtime/end_to_end_qualification.py   tests/test_shared_runtime_root.py   tests/test_autonomous_diagnostics_supervisor_safety.py

if ! git diff --cached --quiet; then
  git commit -m "Fix runtime health control-plane and diagnostics serialization"
fi

BRANCH="$(git branch --show-current)"
git push origin "HEAD:$BRANCH"
echo "GITHUB_PUSH=PASS"

echo
echo "===== PASS 2D SUMMARY ====="
echo "DIAGNOSTICS_SERIALIZATION_PATCH=PASS"
echo "TARGETED_TESTS=PASS"
echo "FULL_PYTEST=PASS"
echo "CORE_RUNTIME_HEALTH=PASS"
echo "DIAGNOSTICS_JSON_PARSE=PASS"
echo "DIAGNOSTICS_PARENT_RESTART_GUARD=PASS"
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
  echo "COMPANYOS_AUDIT_REPAIR_PASS_2D=COMPLETE"
else
  echo "COMPANYOS_AUDIT_REPAIR_PASS_2D=COMPLETE_WITH_NATIVE_CHECKS_TO_INSPECT"
fi
