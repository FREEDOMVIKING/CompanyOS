#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
R="$HOME/.companyos_runtime"; Q="$R/task_queue"; TS="$(date +%Y%m%d_%H%M%S)"
OUT="$R/v44_fresh_failure_forensics_$TS.json"
echo "===== COMPANYOS V44 FRESH FAILURE FORENSICS ====="
echo "QUEUE_RECORDS_DELETED=0"; echo "FINANCE_CONNECTORS_CHANGED=0"; echo "SUPERVISOR_RESTARTED=NO"
python - "$Q" "$OUT" <<'PY'
import json,sys,time,collections
from pathlib import Path
q,out=Path(sys.argv[1]),Path(sys.argv[2])
def snap():
 d={}
 for p in q.glob("*.json"):
  try:
   x=json.loads(p.read_text()); k=str(x.get("task_id") or p.stem)
   d[k]={"state":x.get("state"),"attempts":x.get("attempts",0),"last_error":x.get("last_error"),
         "task_type":x.get("task_type"),"updated":x.get("updated_at_unix",0),"path":str(p)}
  except Exception: pass
 return d
a=snap(); print("BASELINE",dict(collections.Counter(v["state"] for v in a.values())))
time.sleep(60); b=snap(); print("FINAL",dict(collections.Counter(v["state"] for v in b.values())))
changed=[]; fresh=[]
for k,v in b.items():
 old=a.get(k)
 if old!=v: changed.append(k)
 if v.get("last_error") and (not old or old.get("last_error")!=v.get("last_error")): fresh.append((k,v))
sig=collections.Counter(); types=collections.Counter(); sample={}
for k,v in fresh:
 s=str(v["last_error"]).splitlines()[0][:240]; sig[s]+=1; types[v.get("task_type") or "unknown"]+=1
 sample.setdefault(s,(k,v))
report={"changed_records":len(changed),"fresh_error_updates":len(fresh),"fresh_error_types":dict(types),
"signatures":[{"count":n,"task_id":sample[s][0],"task_type":sample[s][1].get("task_type"),
"error":sample[s][1].get("last_error"),"path":sample[s][1].get("path")} for s,n in sig.most_common(20)]}
out.write_text(json.dumps(report,indent=2)+"\n")
print("CHANGED_RECORDS",len(changed)); print("FRESH_ERROR_UPDATES",len(fresh)); print("FRESH_ERROR_TYPES",dict(types))
print("---- TOP FRESH ERROR SIGNATURES ----")
for s,n in sig.most_common(12): print(f"{n}x [{sample[s][1].get('task_type')}] {s}\n  TASK {sample[s][0]}")
print("REPORT="+str(out))
PY
echo "V44_FORENSICS=PASS"
echo "NEXT=send_bottom_output"
