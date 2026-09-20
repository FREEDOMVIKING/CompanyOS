#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
R="$HOME/.companyos_runtime"; Q="$R/task_queue"; TS="$(date +%Y%m%d_%H%M%S)"
B="$R/backups/v43_$TS"; REPORT="$R/v43_recovery_$TS.log"; mkdir -p "$B"
exec > >(tee -a "$REPORT") 2>&1
echo "===== COMPANYOS V43 CONTROLLED RECOVERY + CEO REENTRY ====="
SUP=$(pgrep -af 'companyos/runtime/service_supervisor.py'|grep -v grep|wc -l||true)
CON=$(pgrep -af 'continuous_goal_runtime'|grep -v grep|wc -l||true)
echo "SUPERVISOR_COUNT=$SUP CONTINUOUS_COUNT=$CON"
[ "$SUP" -eq 1 ] && [ "$CON" -eq 1 ] || { echo "ABORT=singleton"; exit 43; }
python -m pytest -q tests/test_v39_dispatch_result_repair.py tests/test_v36_live_recovery_qualification.py tests/test_v34_worker_lease_store.py
echo "REGRESSION=PASS"
python - "$Q" "$B" <<'PY'
import json,sys,shutil,time
from pathlib import Path
q,b=Path(sys.argv[1]),Path(sys.argv[2]); eligible=[]
for f in q.glob("*.json"):
 try:
  d=json.loads(f.read_text())
  e=str(d.get("last_error") or d.get("error") or "")
  if str(d.get("state","")).upper()=="FAILED" and "NameError: name 'result' is not defined" in e:
   eligible.append((f,d))
 except: pass
print("ELIGIBLE="+str(len(eligible)))
for f,d in eligible: shutil.copy2(f,b/f.name)
for f,d in eligible:
 d["state"]="QUEUED"; d["last_error"]=None; d["error"]=None; d["retry_count"]=0
 d["updated_at_unix"]=time.time()
 d.setdefault("recovery_history",[]).append({"at_unix":time.time(),"reason":"v43_exact_repaired_result_nameerror"})
 tmp=f.with_suffix(".v43tmp"); tmp.write_text(json.dumps(d,indent=2,sort_keys=True)); tmp.replace(f)
print("RECOVERED_TO_QUEUE="+str(len(eligible))); print("BACKUP="+str(b))
PY
count(){ python - "$Q" "$1" <<'PY'
import json,sys
from pathlib import Path
n=0
for f in Path(sys.argv[1]).glob("*.json"):
 try:
  if str(json.loads(f.read_text()).get("state","")).upper()==sys.argv[2]: n+=1
 except: pass
print(n)
PY
}
C0=$(count COMPLETED); F0=$(count FAILED); Q0=$(count QUEUED)
echo "BASE COMPLETED=$C0 FAILED=$F0 QUEUED=$Q0"
for t in 60 120 180 240 300 360 420 480 540 600; do
 sleep 60; C=$(count COMPLETED); F=$(count FAILED); QQ=$(count QUEUED)
 echo "T+$t COMPLETED=$C FAILED=$F QUEUED=$QQ completed_delta=$((C-C0)) failed_delta=$((F-F0)) queued_delta=$((QQ-Q0))"
done
C1=$(count COMPLETED); F1=$(count FAILED); Q1=$(count QUEUED)
echo "FINAL_COMPLETED_DELTA=$((C1-C0))"
echo "FINAL_FAILED_DELTA=$((F1-F0))"
echo "FINAL_QUEUED_DELTA=$((Q1-Q0))"
SUP2=$(pgrep -af 'companyos/runtime/service_supervisor.py'|grep -v grep|wc -l||true)
CON2=$(pgrep -af 'continuous_goal_runtime'|grep -v grep|wc -l||true)
echo "SUPERVISOR_COUNT=$SUP2 CONTINUOUS_COUNT=$CON2"
PASS=YES
[ "$SUP2" -eq 1 ] || PASS=NO; [ "$CON2" -eq 1 ] || PASS=NO
[ "$((C1-C0))" -gt 0 ] || PASS=NO; [ "$F1" -le 5 ] || PASS=NO
if [ "$PASS" = YES ]; then echo "V43_RECOVERY=PASS"; echo "CEO_REENTRY_GATE=PASS"; else echo "V43_RECOVERY=NEEDS_DIAGNOSIS"; echo "CEO_REENTRY_GATE=HOLD"; fi
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"
echo "REPORT=$REPORT"
echo "BACKUP=$B"
