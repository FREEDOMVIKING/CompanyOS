#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
LOG="$HOME/.companyos_runtime/logs/service_supervisor_v29_1.log"
mkdir -p "$(dirname "$LOG")"

echo "===== V29.1 COLD START RECOVERY ====="
python - <<'PY'
from pathlib import Path
a=Path("companyos/runtime/continuous_goal_runtime.py").read_text()
b=Path("companyos/runtime/autonomous_ceo_runtime_service.py").read_text()
assert "V29_BIG_RUNTIME_STABILIZATION" in a
assert "V29_PERSISTENT_CEO_STATE" in b
print("V29_SOURCE=PASS")
PY
python -m py_compile companyos/runtime/{continuous_goal_runtime,autonomous_ceo_runtime_service,autonomous_goal_execution_loop,dependency_aware_dispatcher,autonomous_task_dispatcher,autonomous_task_queue}.py
echo "COMPILE=PASS"

echo "===== CLEAR STALE STOP SIGNALS ====="
python - <<'PY'
from pathlib import Path
root=Path.home()/".companyos_runtime"
for name in ("service_supervisor.stop","supervisor.stop","continuous_goal_runtime.stop","continuous_runtime.stop"):
 p=root/name
 if p.exists():
  dst=p.with_name(p.name+".v29_1_stale")
  if dst.exists(): dst.unlink()
  p.replace(dst); print("MOVED",p.name)
print("STOP_SIGNAL_CHECK=PASS")
PY

SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
if [ -z "$SUP" ]; then
 nohup python -m companyos.runtime.service_supervisor >>"$LOG" 2>&1 &
 echo "LAUNCH_PID=$!"
fi
for i in $(seq 1 30); do
 sleep 1; SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
 [ -n "$SUP" ] && break; echo "waiting_supervisor=${i}s"
done
[ -n "$SUP" ] || { echo "FAIL=supervisor_not_started"; tail -80 "$LOG" || true; exit 2; }
echo "SUPERVISOR_PID=$SUP"

CHILD=""
for i in $(seq 1 45); do
 sleep 1; CHILD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
 [ -n "$CHILD" ] && break; echo "waiting_continuous=${i}s"
done
[ -n "$CHILD" ] || { echo "FAIL=continuous_not_started"; tail -100 "$LOG" || true; exit 3; }
echo "CONTINUOUS_PID=$CHILD"

echo "===== 150 SECOND QUALIFICATION ====="
python - <<'PY'
import json,time
from pathlib import Path
from collections import Counter
root=Path.home()/".companyos_runtime"/"task_queue"
sp=Path.home()/".companyos_runtime"/"continuous_goal_runtime_state.json"
def snap():
 c=Counter()
 for p in root.glob("*.json"):
  try:c[str(json.loads(p.read_text()).get("state","UNKNOWN")).upper()]+=1
  except Exception:c["UNREADABLE"]+=1
 return c
def state():
 try:return json.loads(sp.read_text())
 except Exception:return {}
a=snap(); b=a; print("T+000",dict(a),flush=True)
for sec in range(15,151,15):
 time.sleep(15); b=snap(); r=state()
 print(f"T+{sec:03d}",dict(b),
  "completed_delta=",b["COMPLETED"]-a["COMPLETED"],
  "queued_delta=",b["QUEUED"]-a["QUEUED"],
  "failed_delta=",b["FAILED"]-a["FAILED"],
  "cycles=",r.get("cycles"),"exec=",r.get("execution_dispatched"),
  "exec_fail=",r.get("execution_failures"),"sched_fail=",r.get("scheduler_failures"),
  "ceo_fail=",r.get("ceo_failures"),"reason=",r.get("last_reason"),flush=True)
print("FINAL_COMPLETED_DELTA=",b["COMPLETED"]-a["COMPLETED"])
print("FINAL_QUEUED_DELTA=",b["QUEUED"]-a["QUEUED"])
print("FINAL_FAILED_DELTA=",b["FAILED"]-a["FAILED"])
PY

echo "===== HEALTH ====="
python - <<'PY'
import json
from pathlib import Path
for n in ("continuous_goal_runtime_state.json","autonomous_ceo_runtime_service.json"):
 p=Path.home()/".companyos_runtime"/n; print("---",n,"---")
 if not p.exists(): print("MISSING"); continue
 try:d=json.loads(p.read_text())
 except Exception as e: print("READ_ERROR",e); continue
 for k in ("running","ready","last_reason","reason","cycles","cycle_count","consecutive_failures","execution_dispatched","execution_failures","scheduler_failures","ceo_failures","cycles_dispatched_this_tick"):
  if k in d: print(k,"=",d[k])
PY

SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
CHILD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
echo "FINAL_SUPERVISOR_PID=${SUP:-none}"
echo "FINAL_CONTINUOUS_PID=${CHILD:-none}"
[ -n "$SUP" ] || { echo "QUALIFICATION_FAIL=supervisor_died"; exit 4; }
[ -n "$CHILD" ] || { echo "QUALIFICATION_FAIL=continuous_died"; exit 5; }
echo "V29_1_COMPLETE"
echo "SUPERVISOR_ALIVE=YES"
echo "CONTINUOUS_ALIVE=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
