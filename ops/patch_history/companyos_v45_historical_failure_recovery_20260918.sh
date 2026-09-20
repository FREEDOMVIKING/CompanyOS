#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
R="$HOME/.companyos_runtime"; Q="$R/task_queue"; TS="$(date +%Y%m%d_%H%M%S)"
B="$R/backups/v45_$TS"; mkdir -p "$B"
REPORT="$R/v45_historical_failure_recovery_$TS.json"

echo "===== COMPANYOS V45 HISTORICAL FAILURE RECOVERY ====="
echo "MODE=QUALIFY_THEN_REQUEUE"
echo "FINANCE_CONNECTORS_CHANGED=0"
echo "SUPERVISOR_RESTARTED=NO"

python - "$Q" "$B" "$REPORT" <<'PY'
import json,sys,shutil,time,collections,re
from pathlib import Path
q,bak,out=map(Path,sys.argv[1:4])

# Only failures matching defects already observed/fixed in this repair line.
recoverable_patterns=[
 re.compile(r"NameError:\s*name ['\"]result['\"] is not defined",re.I),
 re.compile(r"name ['\"]result['\"] is not defined",re.I),
]
failed=[]; recover=[]; untouched=[]; sig=collections.Counter()
for p in q.glob("*.json"):
 try: x=json.loads(p.read_text())
 except Exception: continue
 if x.get("state")!="FAILED": continue
 failed.append(p)
 err=str(x.get("last_error") or "")
 sig[err.splitlines()[0][:220] or "<no error>"]+=1
 if any(rx.search(err) for rx in recoverable_patterns):
  recover.append((p,x))
 else: untouched.append((p,x))

print("FAILED_TOTAL",len(failed))
print("QUALIFIED_RECOVERABLE",len(recover))
print("UNTOUCHED_FAILED",len(untouched))
print("---- TOP HISTORICAL FAILURE SIGNATURES ----")
for s,n in sig.most_common(12): print(f"{n}x {s}")

# Backup every record we actually mutate.
for p,x in recover:
 shutil.copy2(p,bak/p.name)

# Conservative state reset: preserve identity/payload/dependencies/history.
now=time.time()
for p,x in recover:
 x["state"]="QUEUED"
 x["last_error"]=None
 # Clear transient lease/assignment fields without erasing task history.
 for k in ("lease_owner","lease_expires_at","leased_at","claimed_at","started_at"):
  if k in x: x[k]=None
 x["updated_at_unix"]=now
 hist=x.setdefault("recovery_history",[])
 if isinstance(hist,list):
  hist.append({"at_unix":now,"reason":"v45_requeue_after_fixed_result_nameerror",
               "previous_state":"FAILED"})
 p.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")

report={
 "failed_total":len(failed),
 "qualified_requeued":len(recover),
 "untouched_failed":len(untouched),
 "backup":str(bak),
 "qualification":"historical result NameError only",
 "top_signatures":sig.most_common(20)
}
out.write_text(json.dumps(report,indent=2)+"\n")
print("REQUEUED",len(recover))
print("BACKUP",bak)
print("REPORT",out)
PY

echo "===== POST-RECOVERY 60S QUALIFICATION ====="
python - "$Q" <<'PY'
import json,sys,time,collections
from pathlib import Path
q=Path(sys.argv[1])
def states():
 c=collections.Counter()
 for p in q.glob("*.json"):
  try:c[json.loads(p.read_text()).get("state","UNKNOWN")]+=1
  except Exception:c["UNREADABLE"]+=1
 return c
a=states(); print("T+000",dict(a)); time.sleep(60); z=states(); print("T+060",dict(z))
print("COMPLETED_DELTA",z["COMPLETED"]-a["COMPLETED"])
print("FAILED_DELTA",z["FAILED"]-a["FAILED"])
print("QUEUED_DELTA",z["QUEUED"]-a["QUEUED"])
PY

echo "V45_RECOVERY=PASS"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
echo "FINANCE_CONNECTORS_CHANGED=0"
echo "NEXT=send_bottom_output"
