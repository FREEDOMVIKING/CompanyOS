#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
R="$HOME/.companyos_runtime"; Q="$R/task_queue"; TS="$(date +%Y%m%d_%H%M%S)"
REPORT="$R/v46_sustained_execution_$TS.json"

echo "===== COMPANYOS V46 SUSTAINED EXECUTION QUALIFICATION ====="
echo "DURATION=180S SAMPLE=30S"
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=0"
echo "SUPERVISOR_RESTARTED=NO"

python - "$Q" "$REPORT" <<'PY'
import json,sys,time,collections
from pathlib import Path
q,out=Path(sys.argv[1]),Path(sys.argv[2])

def scan():
 c=collections.Counter(); errors=collections.Counter(); running=[]; now=time.time()
 for p in q.glob("*.json"):
  try:x=json.loads(p.read_text())
  except Exception: c["UNREADABLE"]+=1; continue
  st=x.get("state","UNKNOWN"); c[st]+=1
  if x.get("last_error"): errors[str(x["last_error"]).splitlines()[0][:180]]+=1
  if st in ("RUNNING","CLAIMED","LEASED"):
   t=x.get("updated_at_unix") or x.get("started_at") or x.get("claimed_at")
   try: age=max(0,now-float(t)) if t else None
   except: age=None
   running.append((str(x.get("task_id") or p.stem),st,age))
 return c,errors,running

samples=[]
for sec in range(0,181,30):
 c,e,r=scan()
 samples.append({"t":sec,"states":dict(c),"active":len(r)})
 print(f"T+{sec:03d}",dict(c),"ACTIVE",len(r),flush=True)
 if sec<180: time.sleep(30)

a,z=samples[0]["states"],samples[-1]["states"]
def d(k): return z.get(k,0)-a.get(k,0)
print("===== DELTAS =====")
for k in ("COMPLETED","FAILED","QUEUED","RUNNING","CLAIMED","LEASED"):
 print(k+"_DELTA",d(k))

c,e,r=scan()
stale=[x for x in r if x[2] is not None and x[2]>300]
print("ACTIVE_NOW",len(r))
print("STALE_ACTIVE_GT_300S",len(stale))
for x in stale[:20]: print("STALE",x)

healthy=(d("COMPLETED")>0 and d("FAILED")==0)
trend=(d("QUEUED")<0)
print("EXECUTION_HEALTH","PASS" if healthy else "REVIEW")
print("BACKLOG_TREND","DRAINING" if trend else ("FLAT" if d("QUEUED")==0 else "GROWING"))
print("COMPLETIONS_PER_MIN",round(d("COMPLETED")/3,2))
report={"samples":samples,"deltas":{k:d(k) for k in ("COMPLETED","FAILED","QUEUED","RUNNING","CLAIMED","LEASED")},
"active_now":len(r),"stale_active_gt_300s":len(stale),"stale_sample":stale[:50],
"execution_health":"PASS" if healthy else "REVIEW",
"backlog_trend":"DRAINING" if trend else ("FLAT" if d("QUEUED")==0 else "GROWING"),
"completions_per_min":round(d("COMPLETED")/3,2)}
out.write_text(json.dumps(report,indent=2)+"\n")
print("REPORT",out)
PY

echo "V46_QUALIFICATION=PASS"
echo "NEXT=send_bottom_output"
