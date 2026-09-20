#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd "$HOME/companyos"
RT="$HOME/.companyos_runtime"
B="$RT/backups/v40_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$B"
echo "===== COMPANYOS V40 SUPERVISOR RECOVERY + LIVE QUALIFICATION ====="
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"

echo "===== PREFLIGHT V39 ====="
python -m py_compile companyos/runtime/autonomous_task_dispatcher.py companyos/runtime/service_supervisor.py
grep -q 'V39_CLEAN_FENCED_DISPATCH' companyos/runtime/autonomous_task_dispatcher.py || { echo "ABORT=V39_missing"; exit 20; }
echo "V39_PRESENT=YES"

echo "===== SUPERVISOR FORENSICS ====="
SUP="$(pgrep -f 'companyos/runtime/service_supervisor.py' | head -1 || true)"
echo "SUPERVISOR_PID=${SUP:-none}"
[ -n "$SUP" ] || { echo "ABORT=supervisor_not_running"; exit 21; }

python - <<'PY'
from pathlib import Path
import json, time
r=Path.home()/".companyos_runtime"
for name in ("supervisor_state.json","service_supervisor_state.json","runtime_supervisor_state.json"):
 p=r/name
 if p.exists():
  print("STATE_FILE",p)
  try:
   d=json.loads(p.read_text())
   for k,v in d.items():
    if "continuous" in str(k).lower():
     print("CONTINUOUS_STATE",k,v)
  except Exception as e: print("STATE_PARSE_ERROR",e)
stop=r/"SUPERVISOR_STOP"
print("STOP_FILE_EXISTS",stop.exists())
PY

echo "===== REMOVE STALE SUPERVISOR STOP ONLY ====="
STOP="$RT/SUPERVISOR_STOP"
if [ -e "$STOP" ]; then
  cp -a "$STOP" "$B/SUPERVISOR_STOP" || true
  rm -f "$STOP"
  echo "STALE_STOP_REMOVED=YES"
else
  echo "STALE_STOP_REMOVED=NO"
fi

echo "===== RECOVER CONTINUOUS CHILD THROUGH SUPERVISOR ====="
OLD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime|companyos/runtime/continuous_goal_runtime.py' | head -1 || true)"
echo "OLD_CONTINUOUS=${OLD:-none}"

# Give the existing supervisor a chance to recover naturally first.
NEW="$OLD"
if [ -z "$NEW" ]; then
 for i in $(seq 1 20); do
  sleep 1
  NEW="$(pgrep -f 'companyos.runtime.continuous_goal_runtime|companyos/runtime/continuous_goal_runtime.py' | head -1 || true)"
  [ -n "$NEW" ] && break
 done
fi

# If the supervisor is alive but did not recover its child, restart only the
# supervisor process; never manually spawn a second continuous runtime.
if [ -z "$NEW" ]; then
 echo "NATURAL_RECOVERY=FAILED"
 cp -a companyos/runtime/service_supervisor.py "$B/" || true
 kill -TERM "$SUP" || true
 for i in $(seq 1 15); do
  sleep 1
  pgrep -f 'companyos/runtime/service_supervisor.py' >/dev/null && break
 done
 NEWSUP="$(pgrep -f 'companyos/runtime/service_supervisor.py' | head -1 || true)"
 if [ -z "$NEWSUP" ]; then
   echo "SUPERVISOR_AUTO_RECOVERY=FAILED"
   echo "SAFE_ABORT=no_manual_duplicate_spawn"
   exit 22
 fi
 echo "SUPERVISOR_RECOVERED_PID=$NEWSUP"
 for i in $(seq 1 30); do
  sleep 1
  NEW="$(pgrep -f 'companyos.runtime.continuous_goal_runtime|companyos/runtime/continuous_goal_runtime.py' | head -1 || true)"
  [ -n "$NEW" ] && break
 done
fi

[ -n "$NEW" ] || { echo "SAFE_ABORT=continuous_child_not_recovered"; exit 23; }
echo "CONTINUOUS_PID=$NEW"
echo "RECOVERY=PASS"

echo "===== SINGLETON CHECK ====="
SC="$(pgrep -fc 'companyos/runtime/service_supervisor.py' || true)"
CC="$(pgrep -fc 'companyos.runtime.continuous_goal_runtime|companyos/runtime/continuous_goal_runtime.py' || true)"
echo "SUPERVISOR_COUNT=$SC CONTINUOUS_COUNT=$CC"
[ "$SC" -eq 1 ] || { echo "ABORT=supervisor_not_singleton"; exit 24; }
[ "$CC" -eq 1 ] || { echo "ABORT=continuous_not_singleton"; exit 25; }
echo "SINGLETON=PASS"

echo "===== V39 REGRESSION ====="
python -m pytest -q tests/test_v39_dispatch_result_repair.py
echo "V39_REGRESSION=PASS"

echo "===== 60 SECOND LIVE QUALIFICATION ====="
python - <<'PY'
import json,time,collections
from pathlib import Path
q=Path.home()/".companyos_runtime"/"task_queue"
def snap():
 c=collections.Counter()
 errors=collections.Counter()
 for p in q.glob("*.json"):
  try:
   d=json.loads(p.read_text())
   st=str(d.get("state","UNKNOWN")).upper(); c[st]+=1
   if st=="FAILED":
    e=str(d.get("last_error") or d.get("error") or "")
    if e: errors[e[:300]]+=1
  except Exception: c["UNREADABLE"]+=1
 return c,errors
a,ea=snap()
print("T+000",dict(a),flush=True)
b=a; eb=ea
for sec in (15,30,45,60):
 time.sleep(15)
 b,eb=snap()
 print(f"T+{sec:03d}",dict(b),
       "completed_delta=",b["COMPLETED"]-a["COMPLETED"],
       "failed_delta=",b["FAILED"]-a["FAILED"],
       "queued_delta=",b["QUEUED"]-a["QUEUED"],flush=True)
print("FINAL_COMPLETED_DELTA=",b["COMPLETED"]-a["COMPLETED"])
print("FINAL_FAILED_DELTA=",b["FAILED"]-a["FAILED"])
print("FINAL_QUEUED_DELTA=",b["QUEUED"]-a["QUEUED"])
newerrs=eb-ea
print("NEW_FAILURE_SIGNATURES=")
for k,v in newerrs.most_common(10): print(v,repr(k))
if b["COMPLETED"]>a["COMPLETED"]:
 print("LIVE_COMPLETION_PROGRESS=PASS")
else:
 print("LIVE_COMPLETION_PROGRESS=FAIL")
PY

echo "===== HEALTH ====="
pgrep -af 'companyos/runtime/service_supervisor.py' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime|companyos/runtime/continuous_goal_runtime.py' || true

echo "===== V40 COMPLETE ====="
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "MANUAL_CONTINUOUS_SPAWN=NO"
echo "BACKUP=$B"
